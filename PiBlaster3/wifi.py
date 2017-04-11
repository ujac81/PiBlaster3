"""wifi.py -- modify hostapd.conf file via piadmin interface to change WPA passphrase.

"""
from django.conf import settings
import shutil


def get_wifi_settings():
    """Get ssid and password from current hostapd.conf file.
    Note: Set settings.PB_HOSTAPD_FILE
    :return: {'ssid': 'SSID', 'passwd': 'PASS'}
    """
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
    """Write new hostapd.conf file with new ssid and WPA passphrase.

    NOTE: Set settings.PB_HOSTAPD_FILE
    NOTE: If you mess up anything here, you will no longer see your access point!

    :param ssid: ssid to set in hostapd file.
    :param pass1: WPA passphrase
    :param pass2: confirmation for WPA passphrase (must much pass1)
    """

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

