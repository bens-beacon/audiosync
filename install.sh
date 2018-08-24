# Install required libaries

echo ' ### Install Python-Pip if not available'
sudo apt-get install python-pip libffi-dev libportaudio2

echo ' #### Install PIP Stuff'
pip install sounddevice soundfile ntplib