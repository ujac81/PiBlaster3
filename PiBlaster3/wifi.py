
from django.conf import settings


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
