
from django.conf import settings
import shutil


def get_wifi_settings():
    sets = {'ssid': 'SSID', 'passwd': 'PASS'}

    if settings.PB_HOSTAPD_FILE is None:
        return sets

    with open(settings.PB_HOSTAPD_FILE, 'r') as f:
        for line in f:
            if line.startswith('ssid='):
                sets['ssid'] = line.split('=')[1]
            if line.startswith('wpa_passphrase='):
                sets['passwd'] = line.split('=')[1]

    return sets


def set_wifi_settings(ssid, pass1, pass2):

    # TODO: check ssid and pass for valid chars

    if pass1 != pass2:
        return

    lines = []
    with open(settings.PB_HOSTAPD_FILE, 'r') as f:
        for line in f:
            if line.startswith('ssid='):
                line = 'ssid='+ssid
            if line.startswith('wpa_passphrase='):
                line = 'wpa_passphrase='+pass1
            lines.append(line)

    with open(settings.PB_HOSTAPD_FILE+'.new', 'w') as f:
        for line in lines:
            f.write(line+'\n')

    shutil.copy(settings.PB_HOSTAPD_FILE+'.new', settings.PB_HOSTAPD_FILE)

