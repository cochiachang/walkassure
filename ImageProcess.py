import math
import cv2
import numpy as np
from ultralytics import YOLO
from collections import Counter

# 斑馬線偵測模型
crosswalk_model = YOLO('./model/crosswalk.pt')
# 障礙物偵測模型
yolo_model = YOLO('./model/yolov8n.pt')
# 紅綠燈偵測模型
traffic_light_model = YOLO('./model/traffic_light.pt')

def image_filter(img, degree = 2):
    decrease_img = (255.0/1)*(img/(255.0/1))**degree
    decrease_img = np.array(decrease_img, dtype=np.uint8)
    return decrease_img

def calculate_angle(x1, y1, x2, y2):
    if x2 - x1 == 0:
        return 90  # 垂直線
    angle = math.atan2((y2 - y1), (x2 - x1)) * (180 / np.pi)
    return angle
    
def clock_direction(angle):
    if angle < 0:
        angle += 360
    
    if 0 <= angle < 10:
        return 12
    elif 10 <= angle < 45:
        return 1
    elif 45 <= angle < 75:
        return 2
    elif 75 <= angle <= 90:
        return 3
    elif 90 < angle < 105:
        return 9
    elif 105 <= angle < 135:
        return 10  # same as 4 o'clock
    elif 135 <= angle < 175:
        return 11  # same as 5 o'clock
    elif 175 <= angle < 185:
        return 12
    elif 185 <= angle < 225:
        return 1
    elif 225 <= angle < 255:
        return 2
    elif 255 <= angle < 270:
        return 3
    elif 270 <= angle < 285:
        return 9
    elif 285 <= angle < 315:
        return 10
    elif 315 <= angle < 355:
        return 11
    else:
        return 12

def increase_brightness(image, value):
    new_image = np.maximum(0, image + value)
    new_image = np.clip(image, 0, 255)
    return new_image

def detect_red_rate(image):
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    red_mask = cv2.bitwise_or(cv2.inRange(imageHSV, np.array([0, 50, 5], dtype=np.uint8), np.array([10, 255, 255], dtype=np.uint8)), 
                          cv2.inRange(imageHSV, np.array([135, 50, 40], dtype=np.uint8), np.array([180, 255, 255], dtype=np.uint8)))
    h, w= image.shape[:2]
    rate = np.count_nonzero(red_mask) / (w*h)

    return rate

def detect_green_rate(image):
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(imageHSV, np.array([35, 20, 0], dtype=np.uint8), np.array([90, 255, 255], dtype=np.uint8))
    h, w= image.shape[:2]
    rate = np.count_nonzero(green_mask) / (w*h)

    return rate

# 取得紅綠燈的狀態
def getTrafficLightStatus(image):
    results = traffic_light_model(image, show=False, verbose=False)
    traffic_light_status = "unknow"
    result = list(results)[0]
    for i in range(len(result.boxes)):
        r = result[i].boxes
        if r.data[0].tolist()[4] > 0.5:
            xywh = r.xywh[0].tolist()

            x_center, y_center, width, height = [int(x) for x in xywh[:4]]
            x1 = int(x_center - (width / 2))
            y1 = int(y_center - (height / 2))
            x2 = x1 + width
            y2 = y1 + height
            traffic_light = image[y1:y2, x1:x2, :]
            height, width = traffic_light.shape[:2]
            traffic_light_status = "red" if detect_red_rate(traffic_light) > 0.01 else ("green" if detect_green_rate(traffic_light) > 0.01 else "未知")
            # cv2.imshow("traffic_light", traffic_light)
            # cv2.waitKey(1)
    return traffic_light_status

def is_overlapping(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    if x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2:
        return False
    return True

# 取得障礙物的輪廓
def getObjectContours(image):
    results = yolo_model(image, show=False, verbose=False)
    alert = []
    result = list(results)[0]
    for i in range(len(result.boxes)):
        r = result[i].boxes
        cls = int(r.cls[0].item())
        xywh = r.xywh[0].tolist()
        x_center, y_center, width, height = [int(x) for x in xywh[:4]]
        x1 = int(x_center - (width / 2))
        y1 = int(y_center - (height / 2))
        x2 = int(x1 + width)
        y2 = int(y1 + height)
        if cls in [0,1,2,3,5,7,16,25,26,28]:
            if y2 > image.shape[0]*0.5 and y2 < image.shape[0]*0.95:
                alert.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "cls": cls})
    return alert

# 取得斑馬線的輪廓
def getCrossWalkContours(image):
    results = crosswalk_model(image, show=False, verbose=False)
    results = list(results)[0]
    contours = []
    for i in range(len(results)):
        r = results[i]
        cls = int(r.boxes.cls[0].item())
        if cls == 0 and r.masks is not None:
            contour = r.masks.xy[0].astype(np.int32)
            approx_polygon = cv2.approxPolyDP(cv2.convexHull(contour), 20, True)
            contours.append(approx_polygon)
    return contours

# 取得灰階圖
def getGrayCrossWalk(image, contour):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    mask = np.zeros(gray.shape[:2], np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    gray = cv2.bitwise_and(gray, mask)
    gray = image_filter(gray)
    return gray

def drawCrossWalkLine(image, crosswalk_lines, color):
    for line in crosswalk_lines:
        cv2.line(image, line[0], line[1], color, 3)
    return image

def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def point_to_line_dist(point, line_start, line_end):
    point = np.array(point)
    line_start = np.array(line_start)
    line_end = np.array(line_end)
    return np.linalg.norm(np.cross(line_end - line_start, line_start - point)) / np.linalg.norm(line_end - line_start)


# 判斷是否偏離
def isOffTrack(image, contour):
    x, y, w, h = cv2.boundingRect(contour)
    mask = np.zeros(image.shape[:2], np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    mask = mask[y+10:y+h,x:x+w]
    left_column = mask[:, 0]
    if np.all(left_column == 255):
        return True, 9
    right_column = mask[:, mask.shape[1]-1]
    if np.all(right_column == 255): 
        return True, 3
    return False, None


# 計算斑馬線的角度
def getCrossWalkAngel(gray):
    canny = cv2.Canny(gray, 50, 150, apertureSize=3)
    canny = cv2.dilate(canny, np.ones((8,8),np.uint8), iterations = 1)
    # 使用概率霍夫變換找線段
    lines = cv2.HoughLinesP(canny, 1, np.pi/180, 30, minLineLength=100, maxLineGap=10)
    lines = [] if lines is None else lines
    # 角度列表
    angles = []

    # 計算每一條線段的角度並將其四捨五入到最近的10度
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = calculate_angle(x1, y1, x2, y2)
        rounded_angle = round(angle / 5) * 5
        if max(y1, y2) > gray.shape[0]*0.5:
            angles.append(rounded_angle)
    # 使用Counter來找出最常出現的角度
    counter = Counter(angles)
    if len(counter.most_common(1)) > 0:
        most_common_angle, freq = counter.most_common(1)[0]
    else:
        most_common_angle = 0
        freq = 0
    crosswalk_lines = []
    total_angle = 0
    if freq > 0:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            center = ((x1 + x2)/2, (y1 + y2)/2)
            angle = calculate_angle(x1, y1, x2, y2)
            rounded_angle = round(angle / 5) * 5
            if rounded_angle == most_common_angle:
                isExist = False
                for i in range(len(crosswalk_lines)):
                    crosswalk_line = crosswalk_lines[i]
                    point1 = crosswalk_line[0]
                    point2 = crosswalk_line[1]
                    min_dist = min(
                        point_to_line_dist((x1, y1), point1, point2),
                        point_to_line_dist((x2, y2), point1, point2),
                        point_to_line_dist(point1, (x1, y1), (x2, y2)),
                        point_to_line_dist(point2, (x1, y1), (x2, y2))
                    )
                    if min_dist < 20:
                        isExist = True
                if isExist is False and max(y1, y2) > gray.shape[0]*0.5:
                    total_angle = total_angle + angle
                    crosswalk_lines.append([(x1, y1), (x2, y2), center])
    # drawCrossWalkLine(gray, crosswalk_lines, (0, 0, 0))
    # cv2.imshow("canny", canny)
    # cv2.imshow("gray", gray)
    # cv2.waitKey(1)

    if len(crosswalk_lines) > 1:
        average_angle = total_angle / len(crosswalk_lines)
    else: average_angle = None
    return  average_angle