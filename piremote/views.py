from django.http import HttpResponse
from django.template import loader

from PiBlaster3.mpc import MPC


def index(request):
    template = loader.get_template('piremote/index.pug')
    mpc = MPC()
    context = {'state': mpc.get_currentsong()}
    return HttpResponse(template.render(context, request))

