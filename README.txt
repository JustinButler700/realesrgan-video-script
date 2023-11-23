This script speeds up video upscaling for Real-ESRGAN
First, download a portable executable for Real-ESRGAN here https://github.com/xinntao/Real-ESRGAN
Drop this script into the same directory as the executable.
then run it with :
python3 myScript.py -i VIDEO_TITLE.mp4

If it doesn't work or produces python errors. Install all necessary dependencies:
pip3 install Pillow
pip3 install shutil

# If you encounter the problem that *macOS cannot verify that this app is free from Malware*, you have two options to try:
# 1. Choose *Apple menu* > go to *System Preferences* > choose *Security & Privacy* > tap the General tab > click the *Open Anyway* button.
# 2. OR run command:  `sudo spctl --master-disable`  to disable Gatekeeper.
