"""
File containing every utils functions for reading and writing streams.
"""
import os
import time
import logging as lg
from pathlib import Path
import cv2
import vlc
import pyrealsense2 as rs2
from utils.thread_read import ReaderRealSense
from utils.thread_write import Writer


def get_cameras_id():
    """
    Return a list containing every camera serial number.
    :return: List of str
    """
    devices = rs2.context().query_devices()

    return [dev.get_info(rs2.camera_info.serial_number) for dev in devices]


def synchronize_readers(readers):
    """
    Helper function that clear the queues of all reader to ensure better synchronism between cameras.
    This is helpful when thread take time to start and start filling queues at different times.
    :param readers:     Dict of ReaderRealSense
    :return:            Dict of ReaderRealSense
    """
    for reader in readers.values():
        reader.clear()

    return readers


def check_path(path) -> None:
    """
    Helper function that create directory if not existing.
    :param path:        Path of the directory as str
    """
    if not os.path.exists(path):
        os.mkdir(path)


def create_writer(output_prefix, output_folder, cam_number, cam_fps, input_width, input_height):
    """
    Create a thread object for video writing to speed up writing frames.
    :param output_prefix:       Prefix for the output name
    :param output_folder:       Folder to store video output
    :param cam_number:          Number of cameras to write from
    :param cam_fps:             Input video FPS
    :param input_width:         Width of the input video
    :param input_height:        Height of the input video
    :return: Video writer in separate thread
    """

    output_name = set_output_name(output_prefix, output_folder)
    # Double the width for the output as each NIR + RGB is stacked horizontally
    writer_width = input_width * 2
    # Triple the height as each RGB + NIR is stacked vertically
    writer_height = input_height * cam_number
    writer = Writer(output_name, cam_fps, writer_width, writer_height)

    return writer


def start_readers(cams, input_width, input_height, cam_fps):
    """
    Start one thread for each cameras to speed up reading frames
    :param cams:                List of RealSense cameras serial number
    :param input_width:         Width of the input image
    :param input_height:        Height of the input image
    :param cam_fps:             FPS of the input camera

    :return: Dict of camera reading threads
    """
    readers = {}
    for cam in cams:
        readers[f"reader{cam}"] = ReaderRealSense(cam, input_width, input_height, cam_fps).start()
    readers = synchronize_readers(readers)

    return readers


def stop_readers(readers) -> None:
    """
    Stop every reader from readers dict
    :param readers:     Dict of readers
    """
    for reader in readers.values():
        reader.stop()


def set_output_name(output_prefix, output_folder) -> str:
    """
    Initialize the video output name with prefix if given, else with timestamp.
    :param output_prefix:       Prefix from argparse
    :param output_folder:       Folder from argparse

    :return: Output name as str
    """
    # Create output folder if not existing
    check_path(output_folder)

    if output_prefix is not None:
        output_name = str(Path(output_folder) / (output_prefix + "_" + str(round(time.time())) + ".mp4"))
    else:
        output_name = str(Path(output_folder) / (str(round(time.time())) + ".mp4"))
    lg.info(f"Default output name is: {output_name}")

    return output_name


def get_frames_concat(readers):
    """
    Get all frames from every thread and concatenate them into one single frame.
    :param readers:     Dict of video readers
    :return: OpenCV image
    """
    camera_frames = []

    # Read every reader frame
    for reader in readers.values():
        camera_frames.append(reader.read())

    frames_concat = cv2.vconcat(camera_frames)

    return frames_concat


def record(readers, writer) -> None:
    """
    Simply record directly concatenated images from readers with the writer.

    :param readers:     Camera reader threads
    :param writer:      Video Writer thread
    """
    # Start writer
    writer = writer.start()

    while True:
        try:
            # Get every frame of every camera into a single huge frame
            frames_concat = get_frames_concat(readers)
            # Write this frame in the output video
            writer.write_frame(frames_concat)
        except KeyboardInterrupt:
            writer.stop()
            stop_readers(readers)
            break


def play_vlc(path: str, wait: bool) -> vlc.MediaPlayer:
    """
    Read media using VLC

    :param path:    Path to the media
    :param wait:    Whether to wait for the player to end
    """
    player = vlc.MediaPlayer()
    media = vlc.Media(path)
    player.set_media(media)
    player.set_fullscreen(True)

    # Sleep to let some time for fullscreen to apply
    if wait:
        time.sleep(2)
    player.audio_set_volume(100)
    player.play()
    # Set audio volume
    # Sleep to let to player start before letting the loop start
    if wait:
        time.sleep(5)

    while player.is_playing() and wait:
        time.sleep(1)

    return player
