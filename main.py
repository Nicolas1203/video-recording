"""
Script for recording videos for dataset construction using Faurecia's buck.
"""
import argparse
import os
import sys
import json
import logging as lg
import time
from PyQt5 import QtWidgets
from gui.window import start_interface, stop_interface
from utils.utils import get_cameras_id, start_readers, create_writer, stop_readers, record, play_vlc
from utils.automatic_data_collection import get_IMAP, read_last_email, get_messages_nb

parser = argparse.ArgumentParser(description="Video recording script for buck dataset.")

parser.add_argument("--camera", choices=["all", "from_config"],
                    help="Cameras to use for recording. It can only be all cameras, or cameras from config file."
                         "For the moment, only Real Sense cameras are supported."
                         "TODO: Implement camera loading from config file.")
parser.add_argument("--time", "-t", help="Max duration of capture in seconds.", type=int, default=60)
parser.add_argument("--verbose", "-v", help="Run the code in verbose mode.", action='store_true')
parser.add_argument('--output-prefix',
                    help="Prefix for the output video file. If None is defined, a timestamp will be used.")
parser.add_argument("--output-folder", default="./videos/", help="Folder where to save videos.")
parser.add_argument("--input-width", "-iw", type=int, default=1280, help="Width of every single video stream.")
parser.add_argument("--input-height", "-ih", type=int, default=720, help="Height of every single video stream.")
parser.add_argument("--cam-fps", type=int, default=30, help="FPS of the streaming camera")
parser.add_argument("--display", "-d", dest="display", help="Display whats being recorded.", action="store_true")
parser.add_argument("--no-display", "-nd", dest="display", help="Nothing will be displayed during run.",
                    action="store_false")
parser.add_argument("--no-sound", help="Deactivate audio speech", action="store_true")
parser.add_argument("--no-vid", help="Deactivate demo video", action="store_true")
parser.add_argument("--video-demo", help="Path to the demo video", default="")
parser.add_argument("--audio-script", help="Path to the audio script", default="")
parser.add_argument("--gui", dest="gui", help="Use a Graphical User Interface.", action="store_true")
parser.add_argument("--no-gui", dest="gui", help="Do not use a Graphical User Interface.", action="store_false")
parser.add_argument("--mail-check-freq", help="Number of seconds interval to between each email check", default=2,
                    type=int)
parser.add_argument("--file-output-name", help="Output name as txt", default="test.txt")
parser.add_argument("--email-address", help="Address to send emails to")
parser.add_argument("--passwd", help="password for the email address")
parser.set_defaults(display=False, gui=False)

args = parser.parse_args()

is_email = args.email_address is not None

if args.verbose:
    lg.basicConfig(level=lg.DEBUG)
    lg.warning("Running in VERBOSE MODE.")
else:
    lg.basicConfig(level=lg.INFO)


def main(secs: int, fname: str, mail_action, stored_data=None, stored_hashes=None,
         imap=None):
    hashes = stored_hashes if stored_hashes else {}
    data = stored_data if stored_data else []
    while True:
        time.sleep(secs)
        if not is_email:
            mail_action()
        else:
            nb_messages = get_messages_nb(imap)
            if nb_messages:
                em = read_last_email(imap, nb_messages, hashes)
                if em != -1:
                    mail_action()
                    hashes.update({em["hash"]: {em["uuid"],
                                                em["height"],
                                                em["weight"]}})
                    data.append(em)
                    with open(fname, 'w') as f:
                        json.dump(data, f)
                mail_action()
                hashes.update({em["hash"]: {em["uuid"],
                                            em["height"],
                                            em["weight"]}})
                data.append(em)

                with open(fname, 'w') as f:
                    json.dump(data, f)


def start():
    player = -1
    cams = get_cameras_id()

    # Start cameras readers
    readers = start_readers(cams, args.input_width, args.input_height, args.cam_fps)

    # Start writer
    writer = create_writer(
        args.output_prefix,
        args.output_folder,
        len(cams),
        args.cam_fps,
        args.input_width,
        args.input_height
    )

    if args.display:
        lg.info('Starting interface')
        start_interface(readers, writer, args)
        lg.info("Interface closed")
    else:
        lg.debug('Interface disabled')
        lg.debug("Start demo video")
        if not args.no_vid:
            if os.path.exists(args.video_demo):
                # use wait to wait for the explaination to end before recording
                player = play_vlc(path=args.video_demo, wait=True)
            else:
                raise Exception("Invalid demo video path")
        lg.debug("Start script audio")
        if not args.no_sound:
            if os.path.exists(args.audio_script):
                # Dont use wait to start recording while the instructions are playing
                player = play_vlc(path=args.audio_script, wait=False)
            else:
                raise Exception("Invalid audio script path")
        lg.debug("start recording")
        record(readers, writer)

    shutdown(writer, readers, player)


def shutdown(writer, readers, player=None):
    """
    Helper function that closes all threads, video writers and close all windows
    :param writer:          Video writer thread
    :param readers:         Dict of video reader threads
    :param player:          Vlc player
    """
    lg.warning("Stopping thread and writers")
    if writer:
        writer.stop()
    if readers:
        stop_readers(readers)
    player.stop()


if __name__ == '__main__':
    try:
        main(
            args.mail_check_freq,
            args.file_output_name,
            start,
            imap=get_IMAP(f"{args.email_address}", f"{args.passwd}") if is_email else None
        )
    except KeyboardInterrupt:
        lg.critical("Keyboard Interrupt")
        try:
            stop_interface()
            QtWidgets.QApplication.exit()
            sys.exit(0)
        except SystemExit:
            os._exit(0)
