# Buck recording

----------------------------------- 
Repository for recording videos in buck for dataset creation. The objective is to
record 3 NIR and 3 RGB videos simultaneously from a RealSense camera with a trigger and possibly a small HMI.

This readme and its instructions have been tested on linux 18.04 only.

**Important**

To the best of my knowledge PyRealSense2 in a virtual environment does not work. I recommend installing it globally.

# How to install

-----------------------------------

## Requirements
   
```pip install -r requirements.txt```
   
## Install OpenCV

If you plan to install it for python only, you can do it with pip: `pip install opencv-python`.
Else please refer to the [official OpenCV docmentation](https://docs.opencv.org/trunk/d7/d9f/tutorial_linux_install.html)

## Install PyRealSense2

To install PyRealSense2 on linux, follow these steps:
1. Register the server's public key: 

    `sudo apt-key adv --keyserver keys.gnupg.net --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE`.

In case the public key still cannot be retrieved, check and specify proxy settings: 
`export http_proxy="http://<proxy>:<port>"`, and rerun the command.
2. Add the server to the list of repositories: 
    * Ubuntu 16 LTS: `sudo add-apt-repository "deb http://realsense-hw-public.s3.amazonaws.com/Debian/apt-repo xenial main" -u`
    * Ubuntu 18 LTS: `sudo add-apt-repository "deb http://realsense-hw-public.s3.amazonaws.com/Debian/apt-repo bionic main" -u`
3. Install the libraries (see section below if upgrading packages):

        sudo apt-get install librealsense2-dkms
        sudo apt-get install librealsense2-utils

The above two lines will deploy librealsense2 udev rules, build and activate kernel modules, runtime library and 
executable demos and tools.
4. Optionally install the developer and debug packages: 

        sudo apt-get install librealsense2-dev
        sudo apt-get install librealsense2-dbg

With dev package installed, you can compile an application with librealsense using 
g++ -std=c++11 filename.cpp -lrealsense2 or an IDE of your choice.
5. Install realsense python binding: 

        sudo pip install pyrealsense2

#  How to run

-------------------

## With graphical interface

To start a recording using the gui you can run `python main.py --gui` without any arguments. 
This will display a window with the current video stream.

**Start recording** press the button

**Stop recording** close the window

**top the program** close the window 2 times

**Change the output name** You can optionally fill the text field to specify an output video name in the GUI.
A confirmation window will pop up.

**Using keyboard** You can start a recording using the *space* key. You may need to use *tab* key first.
You have to close the window with the mouse to save the recording.


## Without graphical interface
To run it without displaying images: `python main.py` or `python main.py --no-gui`

## About file naming
By default, every file is named as `<timestamp>.mp4`. The timestamp format is in total seconds, e.g `1597847665.mp4`.

If you add a prefix using the graphical interface or the command arguments, the resulting name will be `<prefix>_<timestamp>.mp4`
e.g `nicolas_1597847665.mp4`.

This is NOT POSSIBLE to register without a timestamp for the moment. This helps ensuring that no video is overwritten accidentally.

# Usage

```bash
usage: main.py [-h] [--camera {all,from_config}] [--time TIME] [--verbose]
               [--output-prefix OUTPUT_PREFIX] [--output-folder OUTPUT_FOLDER]
               [--input-width INPUT_WIDTH] [--input-height INPUT_HEIGHT]
               [--cam-fps CAM_FPS] [--display] [--no-display] [--no-sound]
               [--no-vid] [--video-demo VIDEO_DEMO]
               [--audio-script AUDIO_SCRIPT] [--gui] [--no-gui]
               [--mail-check-freq MAIL_CHECK_FREQ]
               [--file-output-name FILE_OUTPUT_NAME]
               [--email-address EMAIL_ADDRESS] [--passwd PASSWD]

Video recording script for buck dataset.

optional arguments:
  -h, --help            show this help message and exit
  --camera {all,from_config}
                        Cameras to use for recording. It can only be all
                        cameras, or cameras from config file.For the moment,
                        only Real Sense cameras are supported.TODO: Implement
                        camera loading from config file.
  --time TIME, -t TIME  Max duration of capture in seconds.
  --verbose, -v         Run the code in verbose mode.
  --output-prefix OUTPUT_PREFIX
                        Prefix for the output video file. If None is defined,
                        a timestamp will be used.
  --output-folder OUTPUT_FOLDER
                        Folder where to save videos.
  --input-width INPUT_WIDTH, -iw INPUT_WIDTH
                        Width of every single video stream.
  --input-height INPUT_HEIGHT, -ih INPUT_HEIGHT
                        Height of every single video stream.
  --cam-fps CAM_FPS     FPS of the streaming camera
  --display, -d         Display whats being recorded.
  --no-display, -nd     Nothing will be displayed during run.
  --no-sound            Deactivate audio speech
  --no-vid              Deactivate demo video
  --video-demo VIDEO_DEMO
                        Path to the demo video
  --audio-script AUDIO_SCRIPT
                        Path to the audio script
  --gui                 Use a Graphical User Interface.
  --no-gui              Do not use a Graphical User Interface.
  --mail-check-freq MAIL_CHECK_FREQ
                        Number of seconds interval to between each email check
  --file-output-name FILE_OUTPUT_NAME
                        Output name as txt
  --email-address EMAIL_ADDRESS
                        Address to send emails to
  --passwd PASSWD       password for the email address
```

# Architecture
```bash
.
├── audio
│   └── audio_buck.mp3
├── gui
│   ├── simple.ui
│   └── window.py
├── main.py                     // Entrypoint
├── README.md
├── requirements.txt
├── script_audio.md
├── utils
│   ├── automatic_data_collection.py
│   ├── thread_read.py
│   ├── thread_write.py
│   └── utils.py
```

# Generate Doxygen documentation
Install doxygen `sudo apt get install doxygen doxygen-gui`.

Run `doxywizard`. Select buck_recording as working directory, buck_recording as source code directory and scan recursively.

Choose the destination directory you want then click on generate. You can then find the doc as html in the html folder.
CLick on pages.html to navigate through the doc.

# Extract Action Units from video
Data can be automatically annotated using a recording timing table of correspondence.
To extract those action units you can use the standalone script in utils.

# TODO
* memory footprint test
* Add configuration file that can be overloaded with arguments
* Implement support for non-RealSense cameras