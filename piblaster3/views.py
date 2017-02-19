

from django.http import HttpResponse
from django.template import loader
#from django.views.decorators.http import require_http_methods

from piblaster3.mpc import MPC


#@require_safe()
def index(request):
    template = loader.get_template('index.haml')
    mpc = MPC()
    context = mpc.get_currentsong()
    return HttpResponse(template.render(context, request))


#@require_safe()
def browse(request):
    template = loader.get_template('browse.haml')
    path = 'local'
    mpc = MPC()
    context = {'browse': mpc.browse(path)}
    return HttpResponse(template.render(context, request))

