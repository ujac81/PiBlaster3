from django.http import HttpResponse, JsonResponse
from django.template import loader

from PiBlaster3.mpc import MPC


def index(request):
    template = loader.get_template('piremote/index.pug')
    mpc = MPC()
    context = {'state': mpc.get_currentsong()}
    return HttpResponse(template.render(context, request))


# GET /browse/#
# build empty browse view -- document.ready will call POST ajax/browse on base dir.
def browse(request):
    template = loader.get_template('piremote/browse.pug')
    return HttpResponse(template.render({}, request))


# POST /ajax/browse/
def browse_ajax(request):
    dirname = request.POST.get('dirname', None)
    if dirname is not None:
        mpc = MPC()
        data = {'dirname': dirname, 'browse': mpc.browse(dirname)}
        return JsonResponse(data)

    return JsonResponse({})
