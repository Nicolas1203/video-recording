import time
import cv2
from threading import Thread
import logging as lg
import os


class Writer:
    """
    Class that continuously write frames from a VideoCapture object with a dedicated thread.
    Initialize the video writer along with the boolean used to indicate if the thread should be stopped or not.
    Initialize the thread and frame used to store frames read from.
    """
    def __init__(self, name, fps, width, height):
        # Set up codec and output video settings
        # See video_file_name setter for conditions
        self.video_file_name = name
        self.fps = fps
        self.width = width
        self.height = height
        self.codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.output = None
        self.frame = None
        self.stopped = False
        self.started = False
        self.thread = None

    def start(self):
        """
        Start the thread and begin writing
        :return: Writer class
        """
        # Enable to call start multiple times without creating another thread
        if not self.started:
            lg.info(f"Recording output...")
            self.output = cv2.VideoWriter(self.video_file_name,
                                          self.codec,
                                          self.fps,
                                          (self.width, self.height)
                                          )
            self.started = True
            self.thread = Thread(target=self.save, args=())
            self.thread.start()
        return self

    @property
    def video_file_name(self):
        return self.__video_file_name

    @video_file_name.setter
    def video_file_name(self, name):
        """
        Set video file name to save
        :param name:        Name to set as string
        """
        assert type(name) == str
        if len(os.path.basename(name)) < 1:
            raise Warning("Filename too short, set a valid filename")
        else:
            self.__video_file_name = name

    def stop(self):
        """
        Set the stopped attribute to TRUE & release the writer object
        """
        self.stopped = True
        if self.output is not None:
            lg.info(f"Video saved as {self.video_file_name}")
            self.output.release()

    def write_frame(self, frame):
        """
        Set the frame to write to the last one read
        """
        self.frame = frame

    def save(self):
        """
        Loop until the thread stop to get next frame and write the last set frame
        """
        while not self.stopped:
            time.sleep(0.00001)
            if self.frame is not None:
                self.output.write(self.frame)
                self.frame = None
