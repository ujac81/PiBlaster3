from django.http import HttpResponse, JsonResponse
from django.template import loader

from PiBlaster3.commands import Commands
from PiBlaster3.mpc import MPC

from .models import Setting


# GET /
# We only have one get for the main page.
# Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
def index(request):
    template = loader.get_template('piremote/index.pug')
    return HttpResponse(template.render({'page': 'index'}, request))


# GET /pages/(PAGE)
# We only have one get for the main page.
# Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
def pages(request, page):
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


# POST /ajax/plsaction/
def plsaction_ajax(request):
    cmd = request.POST.get('cmd', None)
    plname = request.POST.get('plname', '')
    payload = request.POST.getlist('payload[]', [])
    mpc = MPC()
    return JsonResponse(mpc.playlists_action(cmd, plname, payload))


# GET /ajax/plinfo/
def plinfo_ajax(request):
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlistinfo(0, -1), 'status': mpc.get_status_data()})


# GET /ajax/plshortinfo/
def plshortinfo_ajax(request):
    plname = request.GET.get('plname', '')
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlistinfo_by_name(plname), 'plname': plname})


# GET /ajax/plinfo/POSITION
def plinfo_id_ajax(request, id):
    mpc = MPC()
    return JsonResponse({'result': mpc.playlistinfo_full(id)})


# GET /ajax/plchanges/
def plchanges_ajax(request):
    version = request.GET.get('version', None)
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlist_changes(version), 'status': mpc.get_status_data()})


# POST /ajax/search/
def search_ajax(request):
    search = request.POST.get('pattern', None)
    mpc = MPC()
    return JsonResponse(mpc.search_file(search))


# POST /ajax/fileinfo/
def file_info_ajax(request):
    file = request.GET.get('file', None)
    mpc = MPC()
    return JsonResponse({'info': mpc.file_info(file)})


# POST /ajax/command/
def command_ajax(request):
    cmd = request.POST.get('cmd', None)
    payload = request.POST.getlist('payload[]', [])
    commands = Commands()
    return JsonResponse(commands.perform_command(cmd, payload))


# GET /ajax/settings/
def settings_ajax(request):
    payload = request.GET.getlist('payload[]', [])
    return JsonResponse(Setting.get_settings(payload))


# POST /ajax/set/
def set_ajax(request):
    key = request.POST.get('key', '')
    value = request.POST.get('value', '')
    return JsonResponse(Setting.set_setting(key, value))
