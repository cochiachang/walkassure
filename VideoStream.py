# Import the necessary packages
from threading import Thread
import cv2


class VideoStream:
    """Camera object"""
    def __init__(self, resolution=(1920,1080),framerate=30,camera_index=0):
        # Initialize the USB camera and the camera image stream
        self.stream = cv2.VideoCapture(cv2.CAP_DSHOW + camera_index)
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
        #ret = self.stream.set(5,framerate) #Doesn't seem to do anything so it's commented out

        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	# Create a variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread to read frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
		# Return the most recent frame
        return self.frame

    def stop(self):
		# Indicate that the camera and thread should be stopped
        self.stopped = True
