import VideoStream
import Main
import cv2
import numpy as np
import copy
from ultralytics import YOLO
from collections import Counter


videostream = VideoStream.VideoStream((720, 1280), 30, 0).start()
cam_quit = 0

start_no_cross = 0
is_in_crosswalk = False
previous_direction = 0 
remaining_crossings = 0

def mouse_handler(event, x, y, flags, data):
    if event == cv2.EVENT_LBUTTONDOWN:
        imageHSV = cv2.cvtColor(data, cv2.COLOR_BGR2HSV)
        print(imageHSV[y][x][0],imageHSV[y][x][1],imageHSV[y][x][2])

while cam_quit == 0:
    imageSource = videostream.read()
    data, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings = Main.main(imageSource, start_no_cross, is_in_crosswalk, previous_direction , remaining_crossings)
    print(data)
    image = cv2.resize(imageSource, (540,960))
    cv2.imshow("output", image)
    cv2.setMouseCallback("output", mouse_handler, image)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        cam_quit = 1

videostream.stop()
cv2.destroyAllWindows()
