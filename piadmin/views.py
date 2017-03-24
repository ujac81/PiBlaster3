from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template import loader

from .forms import WifiForm

from PiBlaster3.wifi import get_wifi_settings, set_wifi_settings


# GET /
def index(request):
    template = loader.get_template('piadmin/index.pug')
    return HttpResponse(template.render({}, request))


def wifi(request):
    if request.method == 'POST':
        form = WifiForm(request.POST)
        if form.is_valid():
            ssid = form.cleaned_data["ssid"]
            wpa = form.cleaned_data["wpa"]
            wpa_conf = form.cleaned_data["wpa_conf"]
            set_wifi_settings(ssid, wpa, wpa_conf)
            return HttpResponseRedirect('/piadmin/wifi')
    else:
        wifi = get_wifi_settings()
        template = loader.get_template('piadmin/wifi.pug')
        return HttpResponse(template.render(wifi, request))


def delete(request):
    template = loader.get_template('piadmin/delete.pug')
    return HttpResponse(template.render({}, request))


def deleteup(request):
    template = loader.get_template('piadmin/deleteup.pug')
    return HttpResponse(template.render({}, request))

