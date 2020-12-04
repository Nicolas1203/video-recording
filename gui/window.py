"""
Script for GUI
"""
from PyQt5 import QtCore, QtGui, uic
import cv2
import threading
from queue import Queue
from utils.utils import get_frames_concat, set_output_name
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QWidget, QApplication, QLineEdit, QLabel, QGridLayout

# Necessary global variables used to stop and start loops inside threads
running = False
recording = False
video_thread = None
FormClass = uic.loadUiType("./gui/simple.ui")[0]
q = Queue()


class MainWindow(QMainWindow, FormClass):
    """
    GUI class for managing the main window containing a video widget and one button for recording.
    Shared inheritance is used to have a default UI layout and widgets. Code could be re-written to remove form_class
    inheritance.
    """
    def __init__(self, writer, args, win_width=2000, win_height=1000, parent=None):
        """
        :param writer:      Video writer object
        :param args:        Argparser arguments
        :param win_width:   Window width in pxl
        :param win_height:  Window height in pxl
        :param parent:      See Qt doc
        """
        super().__init__(parent)
        self.setupUi(self)

        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()

        # Recording button
        self.startButton.clicked.connect(self.start_clicked)
        self.startButton.setText('CLICK HERE OR PRESS SPACE TO RECORD')

        # video writer
        self.writer = writer

        # argsparser arguments
        self.args = args

        # Window display and dimensions
        self.initUI()

        # Video streaming display
        # self.ImgWidget.setGeometry(100, 100, self.window_width - 200, self.window_height - 200)
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        self.timer = QtCore.QTimer(self)
        # run update_frame at a specific frequency
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)
        video_thread.start()

    def initUI(self):

        # Create textbox
        self.textbox = QLineEdit(self)
        self.textbox.move(20, self.args.input_height + 20)
        self.textbox.resize(280, 40)

        # Create textbox Label
        self.label_textbox = QLabel(self)
        self.label_textbox.setText("Enter the name of the video to register:")
        self.label_textbox.move(20, self.args.input_height - 20)
        self.label_textbox.resize(280,40)

        self.setGeometry(1000, 1000, 1000, 1000)

    def start_clicked(self):
        """
        Action when clicking on the record button
        """
        global recording
        recording = True
        self.startButton.setEnabled(False)
        self.startButton.setText('Starting...')

    def update_frame(self):
        """
        Loop for continuously displaying video
        """
        if not q.empty() and running:
            if recording:
                self.startButton.setText('RECORDING - Close the window to save the video')
            else:
                self.startButton.setText('CLICK HERE TO RECORD')

            # Get frame from queue filled in a separated thread
            frame = q.get()

            img_height, img_width, img_colors = frame.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.ImgWidget.set_image(image)

    @pyqtSlot()
    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        """
        Get video output file name from GUI
        """
        # Get text from interface
        test_box_value = self.textbox.text()

        # Set new video name
        self.writer.video_file_name = set_output_name(test_box_value, self.args.output_folder)
        # Check name length
        if len(test_box_value) < 1:
            QMessageBox.question(
                self,
                'Message - pythonspot.com',
                "Please type a valid name",
                QMessageBox.Ok,
                QMessageBox.Ok
            )
        else:
            # Confirmation message window
            QMessageBox.question(
                self,
                'Message - pythonspot.com', f"Video name set to: {self.writer.video_file_name}",
                QMessageBox.Ok,
                QMessageBox.Ok
            )
        # Reset text field
        self.textbox.setText("")

    def closeEvent(self, event):
        """
        Action when closing the window
        :param event:
        :return:
        """
        global running
        running = False


class OwnImageWidget(QWidget):
    """
    Video widget class that enable to insert video frames into the Main Window
    """
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def set_image(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()


def grab_frames(readers, writer):
    """
    Read and write frames. This function is called in a separated thread.
    :param readers:     List of video readers objects
    :param writer:      Video writer object
    :return:
    """
    while running:
        # Get every frame of every camera into a single huge frame
        frames_concat = get_frames_concat(readers)

        if recording:
            # Write this frame in the output video
            # start method is effective on first call only, does nothing afterwards
            writer = writer.start()
            writer.write_frame(frames_concat)

        q.put(frames_concat)


def start_interface(readers, writer, args) -> None:
    """
    Start a PyQt interface to interact in a more user-friendly manner with the recording.
    :param readers:     Camera reader threads
    :param writer:      Video Writer thread
    :param args:        Argparser arguments
    """
    global video_thread
    global running
    global recording
    running = True

    video_thread = threading.Thread(target=grab_frames, args=(readers, writer))

    app = QApplication([])
    w = MainWindow(writer, args)
    w.setWindowTitle('Video Recording Window')
    w.show()
    app.exec_()
    if writer is not None:
        writer.stop()
    recording = False


def stop_interface():
    """
    Stop remaining thread of the graphical interface
    TODO: update this function
    """
    global running
    running = False
