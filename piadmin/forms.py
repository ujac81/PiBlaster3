

from django import forms


class WifiForm(forms.Form):
    ssid = forms.CharField(label='SSID', max_length=20, min_length=3)
    wpa = forms.CharField(label='WPA', max_length=20, min_length=3)
    wpa_conf = forms.CharField(label='WPA Conf', max_length=20, min_length=3)

