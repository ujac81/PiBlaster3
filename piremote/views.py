from django.http import HttpResponse, JsonResponse
from django.template import loader

from PiBlaster3.mpc import MPC


# GET /
# We only have one get for the main page.
# Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
def index(request):
    template = loader.get_template('piremote/index.pug')
    return HttpResponse(template.render({'page': 'index'}, request))


# GET /pages/(PAGE)
# We only have one get for the main page.
# Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
def page(request, page):
    template = loader.get_template('piremote/index.pug')
    return HttpResponse(template.render({'page': page}, request))


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
    return JsonResponse(mpc.exec_command(cmd))


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
    return JsonResponse({'pl': mpc.playlistinfo(0, -1), 'status': mpc.get_status_data()})


# GET /ajax/plchanges/
def plchanges_ajax(request):
    version = request.GET.get('version', None)
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlist_changes(version), 'status': mpc.get_status_data()})
