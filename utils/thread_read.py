import time
from threading import Thread
from queue import Queue
import pyrealsense2 as rs2
import cv2
import numpy as np

ACCEPTED_WIDTHS = [640, 1280, 1920]
ACCEPTED_HEIGHTS = [480, 720, 1080]
ACCEPTED_DIMS = [str(ACCEPTED_WIDTHS[i]) + "x" + str(ACCEPTED_HEIGHTS[i]) for i in range(len(ACCEPTED_WIDTHS))]
ACCEPTED_FPS = [30, 60]


class ReaderRealSense:
    """
    Class that continuously gets frames from a RealSense camera with a dedicated thread.
    Initialize the pyrealsense pipeline and camera configuration
    Initialize the queue used to store frames read from.
    Return one RGB and one NIR frame at the same time.
    """

    def __init__(self, serial_number, width=640, height=480, fps=30, disable_projector=True, nir_id=1):
        self.serial_number = serial_number

        # Set camera parameters
        # see width setter for conditions
        self.width = width
        # see height setter for conditions
        self.height = height
        # see fps setter for conditions
        self.fps = fps
        self.nir_id = nir_id

        # Initialize RealSense pipeline, context and config
        self.pipeline = rs2.pipeline()
        self.ctx = rs2.context()
        self.config = rs2.config()
        self.setup_config()

        # Boolean for stopping thread
        self.stopped = False

        # Select desired RealSense camera
        self.profile = self.pipeline.start(self.config)
        self.device = self.profile.get_device()

        # Disable pattern projector for NIR
        self.disable_projector = disable_projector
        if self.disable_projector:
            self.disable_pattern_projector()

        # Initialize first frames
        self.frames = self.pipeline.wait_for_frames()

        # initialize the queue used to store frames read from the video file
        self.queue = Queue(maxsize=64)

        # Init thread attribute
        self.thread = None

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if width in ACCEPTED_WIDTHS:
            self.__width = width
        else:
            raise Warning(f"Invalid image width, please use one of the following dimensions: {ACCEPTED_DIMS}")

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        if height in ACCEPTED_HEIGHTS:
            self.__height = height
        else:
            raise Warning(f"Invalid image height, please use one of the following dimensions: {ACCEPTED_DIMS}")

    @property
    def fps(self):
        return self.__fps

    @fps.setter
    def fps(self, fps):
        if fps in ACCEPTED_FPS:
            self.__fps = fps
        else:
            raise Warning(f"Invalid FPS for recording, please use one of the following FPS: {ACCEPTED_FPS}")

    def setup_config(self) -> None:
        """
        Setup RealSense camera configuration, select camera by serial number, set width, fps, color.
        Select nir (right or left).
        """
        self.config.enable_device(self.serial_number)
        self.config.enable_stream(rs2.stream.color, self.width, self.height, rs2.format.rgb8, self.fps)
        self.config.enable_stream(rs2.stream.infrared, self.nir_id, self.width, self.height, rs2.format.y8, self.fps)

    def start(self):
        """
        Start the thread for reading
        :return:    Reader class
        """
        self.thread = Thread(target=self.get, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def stop(self):
        """
        Set to TRUE the stopped attribute to stop de main loop
        """
        self.stopped = True

    def get(self):
        """
        Loop until the thread stop to get next frame
        """
        while not self.stopped:
            time.sleep(0.0001)
            if not self.queue.full():
                # Read last frames
                self.frames = self.pipeline.wait_for_frames()

                # get color frames
                color_frame = self.get_color_frame()

                # get nir frame
                nir_frame = self.get_nir_frame()

                color_nir_frame = np.hstack((color_frame, nir_frame))

                # add the frame to the queue
                self.queue.put(color_nir_frame)

    def read(self):
        """
        Return next frame in the queue. Wait for next frame if not available.
        :return: OpenCV image
        """
        return self.queue.get(block=True)

    def disable_pattern_projector(self):
        """
        Disable the pattern projector for NIR camera
        """
        # Disable pattern projector
        sensors = self.device.query_sensors()
        sensors[0].set_option(rs2.option.emitter_enabled, False)

    def get_color_frame(self):
        """
        Get RealSense RGB frame from frames list
        :return: numpy array RGB color frame
        """
        return cv2.cvtColor(np.asanyarray(self.frames.get_color_frame().get_data()), cv2.COLOR_BGR2RGB)

    def get_nir_frame(self, nir_id=0):
        """
        Get RealSens NIR frame
        :return: numpy array NIR frame
        """
        return cv2.cvtColor(np.asanyarray(self.frames.get_infrared_frame(nir_id).get_data()), cv2.COLOR_GRAY2RGB)

    def clear(self) -> None:
        """
        Clear all elements of the queue. Useful for synchronizing queue initialization on different threads.
        """
        self.queue.queue.clear()
