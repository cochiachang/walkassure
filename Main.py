import ImageProcess
import cv2
import numpy as np
import copy
import time
from collections import Counter

def main(imageSource, start_no_cross, is_in_crosswalk, previous_direction , remaining_crossings, detect_traffic = False):
    start = time.time()
    image = copy.deepcopy(imageSource)
    image = cv2.resize(image, (540, 960))
    current_crosswalk = None
    # 斑馬線判斷
    contours = ImageProcess.getCrossWalkContours(image)
    crosswalkDetect = 0
    message = {"crosswalk_detect": "", "crosswalk_direction": "", "traffic_light": "", "obstacle":""}
    message["crosswalk_detect"] = "no_crosswalk" if len(contours) == 0 else "one_crosswalk" if len(contours) == 1 else "multi_crosswalk"
    for i in range(len(contours)):
        contour = contours[i]
        #判斷是不是正在走的斑馬線
        x, y, w, h = cv2.boundingRect(contour)
        gray_crosswalk = ImageProcess.getGrayCrossWalk(image, contour)
        angle = ImageProcess.getCrossWalkAngel(gray_crosswalk)
        if angle is None:
            clock = "unknow_direction"
        else:
            clock = ImageProcess.clock_direction(angle) 
        if x+w < 540*0.6:
            clock = 9
        elif x > 540*0.4:
            clock = 3
        if y + h > image.shape[0] * 0.8: # 正在走的
            isOffTrack, direction = ImageProcess.isOffTrack(image, contour)
            if isOffTrack is True:
                clock = direction
            current_crosswalk = contour
            if is_in_crosswalk is False:
                is_in_crosswalk = True
            start_no_cross = 0
            message["crosswalk_detect"]  = "start_crosswalk"
            message["crosswalk_direction"] = "unknow_direction" if clock == "unknow_direction" else "clock" + str(clock if clock > 0 else 12+clock) + "_direction"
            remaining_crossings = h / image.shape[0]
            if clock != "unknow_direction": # and clock < 3 and clock > -3:
                previous_direction = clock
            crosswalkDetect = 1
        elif is_in_crosswalk is False:
            message["crosswalk_detect"]  = "near_crosswalk" if y + h > image.shape[0] * 0.4 else "far_crosswalk"
            crosswalkDetect = 1
    # 偵測不到斑馬線時的邏輯判斷
    if crosswalkDetect == 0:
        if start_no_cross == 0: # 計算看不見多久
            start_no_cross = time.time()
        if is_in_crosswalk is True:
            # 判斷是否斑馬線已結束
            if remaining_crossings > 0.3:
                pointer_direction = str(previous_direction if previous_direction > 0 else 12+previous_direction)
                message["crosswalk_detect"]  = "wrong_direction"
                message["crosswalk_direction"] = f"back_clock{pointer_direction}_direction"
            else:
                message["crosswalk_detect"]  = "end_crosswalk"
        else:
            message["crosswalk_detect"]  = "end_crosswalk"
        if time.time() - start_no_cross > 10:
            is_in_crosswalk = False
            message["crosswalk_detect"]  = "no_crosswalk"
    # 障礙物
    alert = ImageProcess.getObjectContours(image)
    cls_values = [item["cls"] for item in alert]
    cls_counts = Counter(cls_values)
    obstacle = []
    if len(alert) > 0:
        obstacle.append("obstacle")
    for key in cls_counts:
        type = {"0": "person", "1": "bicycle", "2": "car", "3": "motorcycle", "5": "bus", "7": "truck", "15": "cat", "16": "dog", "25": "umbrella", "26": "handbag", "28": "suitcase"}
        obstacle.append (type[str(key)])
           
        message["obstacle"] = obstacle
    if detect_traffic is True:
        message["traffic_light"] = "traffic_" + ImageProcess.getTrafficLightStatus(imageSource)
    else:
        message["traffic_light"] = ""
        
    #print(objectData)
    # "0": "person", "1": "bicycle", "2": "car", "3": "motorcycle", "5": "bus", "7": "truck", 
    # "15": "cat", "16": "dog", "25": "umbrella", "26": "handbag", "28": "suitcase"
    # print(time.time() - start)
    #print(message)
    return message, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings