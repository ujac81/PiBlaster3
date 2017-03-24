"""settins_piremote.py -- internal piremote settings.

imported at the end of settings.py

DO NOT OVERWRITE DJANGO SETTINGS HERE
"""

# input required for confirm dialogs (delete playlist, etc)
PB_CONFIRM_PASSWORD = 'ullipw'

# Directory to store uploaded files inside.
# Make sure this one is scanned by MPD or songs won't appear in player.
# Make sure directory exists and is writeable by the user running this server.
# Make sure directory is readable by mpd user.
PB_UPLOAD_DIR = '/var/lib/mpd/music/Upload'

# use 'sudo' if amixer
PB_ALSA_SUDO_PREFIX = ''

# use channel names in alsamixer
PB_ALSA_CHANNELS = ['Master']


# List of directories to use as upload source.
# If automount is installed for raspbian, this should be like (/media/usb0, /media/usb1, ...)
PB_UPLOAD_SOURCES = ['/mnt/usb', '/local']


PB_HOSTAPD_FILE = '/opt/PiBlaster3/conf/hostapd.conf'