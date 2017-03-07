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


# GET /playlist/#
# build empty playlist view -- document.ready will call GET ajax/plinfo
def playlist(request):
    template = loader.get_template('piremote/playlist.pug')
    return HttpResponse(template.render({}, request))


# POST /ajax/browse/
def browse_ajax(request):
    dirname = request.POST.get('dirname', None)
    if dirname is not None:
        mpc = MPC()
        data = {'dirname': dirname, 'browse': mpc.browse(dirname)}
        return JsonResponse(data)

    return JsonResponse({})


# GET /ajax/status/
def status_ajax(request):
    mpc = MPC()
    return JsonResponse(mpc.get_status_data())


# POST /ajax/cmd/
def cmd_ajax(request):
    cmd = request.POST.get('cmd', None)
    mpc = MPC()
    return JsonResponse(mpc.exex_command(cmd))


# POST /ajax/plaction/
def plaction_ajax(request):
    cmd = request.POST.get('cmd', None)
    plname = request.POST.get('plname', '')
    items = request.POST.getlist('list[]', [])
    mpc = MPC()
    return JsonResponse({'status': mpc.playlist_action(cmd, plname, items)})


# GET /ajax/plinfo/
def plinfo_ajax(request):
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlistinfo(0, -1)})
