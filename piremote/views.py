"""views.py -- process GET and POST requests via django.

Invoked via urls.py
"""
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template import loader
from django.conf import settings
from django.core import serializers
import datetime
import json

from PiBlaster3.alsa import AlsaMixer
from PiBlaster3.commands import Commands
from PiBlaster3.helpers import *
from PiBlaster3.mpc import MPC
from PiBlaster3.upload import Uploader
from PiBlaster3.ratings_parser import RatingsParser
from PiBlaster3.history_parser import HistoryParser
from PiBlaster3.smart_playlist import ApplySmartPlaylist
from PiBlaster3.upload_smart_playlist import SmartPlaylistUploader

from .models import Setting, Upload, History, Rating, SmartPlaylist, SmartPlaylistItem
from .forms import UploadForm, UploadRatingsForm, UploadHistoryForm, UploadSmartPlaylistForm


def index(request):
    """GET /
    We only have one get for the main page.
    Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
    """
    return pages(request, 'index')


def pages(request, page):
    """GET /pages/(PAGE)
    We only have one get for the main page.
    Sub pages are dynamical loaded via AJAX and inner page content is rebuilt by d3.js.
    """
    return return_page(request, page)


def return_page(request, page, add_context=dict()):
    template = loader.get_template('piremote/index.pug')
    context = dict(page=page,
                   debug=1 if settings.DEBUG else 0,
                   has_pw=0 if settings.PB_CONFIRM_PASSWORD is '' else 1)
    context.update(add_context)
    return HttpResponse(template.render(context, request))


def list_ajax(request, what):
    """GET /ajax/list/WHAT/ 
    """
    result = dict(data=[])
    raise_working_led()
    if what == 'smart_playlists':
        q = SmartPlaylist.objects.all().order_by('title')
        result['data'] = [[x.id, x.title, x.time.strftime('%a %d %b %Y')] for x in q]
        result['choices'] = SmartPlaylistItem.TYPE_CHOICES
        result['genres'] = Rating.get_distinct('genre')
        result['dates'] = Rating.get_distinct('date')
        result['artists'] = Rating.get_distinct('artist')
    elif what == 'smart_playlist':
        idx = request.GET.get('id')
        result['data'] = SmartPlaylistItem.get_by_id(idx)
    else:
        result['error_str'] = 'Cannot list: '+what
    clear_working_led()
    return JsonResponse(result)


def browse_ajax(request):
    """POST /ajax/browse/
    List directories from MPD lsinfo.
    :return: JSON only -- use with ajax!
    """
    dirname = request.POST.get('dirname', None)
    if dirname is not None:
        raise_working_led()
        mpc = MPC()
        data = {'dirname': dirname, 'browse': mpc.browse(dirname)}
        clear_working_led()
        return JsonResponse(data)

    return JsonResponse({})


def status_ajax(request):
    """GET /ajax/status/
    Status data from MPD (status + currentsong)
    :return: JSON only -- use with ajax!
    """
    mpc = MPC()
    return JsonResponse(mpc.get_status_data())


def cmd_ajax(request):
    """POST /ajax/cmd/
    Perform command for MPD (playpause, next, volinc, ....)
    :return: JSON only -- use with ajax!
    """
    cmd = request.POST.get('cmd', None)
    mpc = MPC()
    flash_command_led()
    return JsonResponse(mpc.exec_command(cmd))


def plaction_ajax(request):
    """POST /ajax/plaction/
    Perform action on one playlist.
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    cmd = request.POST.get('cmd', None)
    plname = request.POST.get('plname', '')
    items = request.POST.getlist('list[]', [])
    mpc = MPC()
    action = mpc.playlist_action(cmd, plname, items)
    clear_working_led()
    return JsonResponse({'status_str': action})


def plsaction_ajax(request):
    """POST /ajax/plsaction/
    Perform action on list of playlists.
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    cmd = request.POST.get('cmd', None)
    plname = request.POST.get('plname', '')
    payload = request.POST.getlist('payload[]', [])
    mpc = MPC()
    action = mpc.playlists_action(cmd, plname, payload)
    clear_working_led()
    return JsonResponse(action)


def plinfo_ajax(request):
    """GET /ajax/plinfo/
    Get current playlist (detailed list).
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    mpc = MPC()
    res = {'pl': mpc.playlistinfo(0, -1), 'status': mpc.get_status_data()}
    clear_working_led()
    return JsonResponse(res)


def plshortinfo_ajax(request):
    """GET /ajax/plshortinfo/
    Get items of stored playlist (fewer data than current playlist)
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    plname = request.GET.get('plname', '')
    mpc = MPC()
    res = {'pl': mpc.playlistinfo_by_name(plname), 'plname': plname}
    clear_working_led()
    return JsonResponse(res)


def plinfo_id_ajax(request, id):
    """GET /ajax/plinfo/POSITION
    Get detailed information about specific playlist item.
    :return: JSON only -- use with ajax!
    """
    mpc = MPC()
    return JsonResponse({'result': mpc.playlistinfo_full(id)})


def plchanges_ajax(request):
    """GET /ajax/plchanges/
    Get list of changes in playlist since version N.
    :return: JSON only -- use with ajax!
    """
    version = request.GET.get('version', None)
    mpc = MPC()
    return JsonResponse({'pl': mpc.playlist_changes(version), 'status': mpc.get_status_data()})


def search_ajax(request):
    """POST /ajax/search/
    Perform search for pattern.
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    search = request.POST.get('pattern', None)
    mpc = MPC()
    res = mpc.search_file(search)
    clear_working_led()
    return JsonResponse(res)


def file_info_ajax(request):
    """POST /ajax/fileinfo/
    Get detailed info by filename.
    :return: JSON only -- use with ajax!
    """
    file = request.GET.get('file', None)
    mpc = MPC()
    return JsonResponse({'info': mpc.file_info(file)})


def command_ajax(request):
    """POST /ajax/command/
    Perform command like 'shutdown' or 'updatedb'
    :return: JSON only -- use with ajax!
    """
    cmd = request.POST.get('cmd', None)
    payload = request.POST.getlist('payload[]', [])
    commands = Commands()
    if cmd == 'settime':
        Setting.set_setting('time_updated', '1')
    flash_command_led(0.5)
    return JsonResponse(commands.perform_command(cmd, payload))


def settings_ajax(request):
    """GET /ajax/settings/
    Get settings list from database.
    :return: JSON only -- use with ajax!
    """
    payload = request.GET.getlist('payload[]', [])
    return JsonResponse(Setting.get_settings(payload))


def set_ajax(request):
    """POST /ajax/set/
    Set settings value in database.
    :return: JSON only -- use with ajax!
    """
    key = request.POST.get('key', '')
    value = request.POST.get('value', '')
    flash_command_led(0.2)
    return JsonResponse(Setting.set_setting(key, value))


def mixer_ajax(request):
    """GET /ajax/mixer/
    Get mixer channels and values for specific class.
    :return: JSON only -- use with ajax!
    """
    mixer_class = request.GET.get('class')
    mixer = AlsaMixer()
    return JsonResponse(mixer.get_channel_data(mixer_class))


def mixerset_ajax(request):
    """POST /ajax/mixerset/
    Set specific mixer value.
    :return: JSON only -- use with ajax!
    """
    mixer_class = request.POST.get('class')
    mixer_channel = int(request.POST.get('channel'))
    mixer_value = int(request.POST.get('value'))
    mixer = AlsaMixer()
    flash_command_led()
    return JsonResponse(mixer.set_channel_data(mixer_class, mixer_channel, mixer_value))


def upload(request):
    """POST /upload
    Handle file upload form.
    :return: upload page including status message about successful upload.
    """
    if request.method == 'POST':
        raise_working_led()
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            raise_upload_led()
            name = form.cleaned_data["uploader"]
            filename = form.cleaned_data["mediafile"]
            up = Uploader()
            res = up.upload_file(name, filename, request.FILES['mediafile'])
            clear_upload_led()
        else:
            res = {'error_str': 'Upload form data is invalid!'}
        clear_working_led()
        return return_page(request, 'upload', {'upload': json.dumps(res)})
    else:
        return HttpResponseRedirect('/piremote/pages/upload')


def upload_smartpl(request):
    """POST /upload/smartpl
    Handle file upload for smart playlist files.
    :return: Redirect to smart playlists.
    """
    if request.method == 'POST':
        raise_working_led()
        form = UploadSmartPlaylistForm(request.POST, request.FILES)
        if form.is_valid():
            raise_upload_led()
            playlist = form.cleaned_data["playlist"]
            filename = form.cleaned_data["mediafile"]
            up = SmartPlaylistUploader()
            res = up.upload(playlist, filename, request.FILES['mediafile'])
            clear_upload_led()
        else:
            res = {'error_str': 'Upload form data is invalid!'}
        clear_working_led()
        return return_page(request, 'smart', {'upload': json.dumps(res)})
    else:
        return HttpResponseRedirect('/piremote/pages/smart')


def upload_ajax(request):
    """POST /ajax/upload/
    Browse USB flash drives for uploadable content.
    :return: JSON only -- use with ajax!
    """
    if Upload.has_uploads():
        return JsonResponse({'uploads': Upload.get_uploads()})

    dirname = request.POST.get('dirname', '').replace('//', '/')
    if dirname is not None:
        flash_command_led()
        up = Uploader()
        return JsonResponse(up.list_dir(dirname))
    return JsonResponse({})


def doupload_ajax(request):
    """POST /ajax/doupload/
    Enqueue file/dir uploads from USB flash drive to database.
    :return: JSON only -- use with ajax!
    """
    paths = request.POST.getlist('paths[]', [])
    if paths is not None:
        flash_command_led()
        up = Uploader()
        return JsonResponse(up.add_to_uploads(paths))
    return JsonResponse({})


def stats_ajax(request):
    """POST /ajax/stats/
    Get statistics for settings view.
    :return: JSON only -- use with ajax!
    """
    mpc = MPC()
    return JsonResponse({'stats': mpc.get_stats()})


def listby_ajax(request):
    """GET /ajax/list
    List items for browse by tags
    :return: JSON only -- use with ajax!
    """
    what = request.GET.get('what', '')
    ratings = request.GET.getlist('ratings[]', [])
    dates = request.GET.getlist('dates[]', [])
    genres = request.GET.getlist('genres[]', [])
    artists = request.GET.getlist('artists[]', [])
    albums = request.GET.getlist('albums[]', [])
    raise_working_led()
    mpc = MPC()
    browse = mpc.list_by(what, ratings, dates, genres, artists, albums)
    context = dict(what=what, browse=browse, truncated=mpc.truncated)
    clear_working_led()
    return JsonResponse(context)


def seed_browse_ajax(request):
    """POST /ajax/seedbrowse
    Perform seed to playlist by selection from browse by tags.
    :return: JSON only -- use with ajax!
    """
    raise_working_led()
    what = request.POST.get('what', '')
    count = int(request.POST.get('count', ''))
    plname = request.POST.get('plname', '')
    ratings = request.POST.getlist('ratings[]', [])
    dates = request.POST.getlist('dates[]', [])
    genres = request.POST.getlist('genres[]', [])
    artists = request.POST.getlist('artists[]', [])
    albums = request.POST.getlist('albums[]', [])
    mpc = MPC()
    res = {'status_str': mpc.seed_by(count, plname, what, ratings, dates, genres, artists, albums)}
    clear_working_led()
    return JsonResponse(res)


def history_ajax(request):
    """GET /ajax/history

    :param request:
    :return:
    """
    raise_working_led()
    mode = request.GET.get('mode')
    title = 'Player History'
    if mode == 'search':
        pattern = request.GET.get('pattern')
        return JsonResponse({'history': History.search_history(pattern), 'mode': mode, 'title': 'Search result'})
    if mode != 'dates':
        title = datetime.datetime.strptime(mode, '%Y-%m-%d').strftime('%A %d %B %Y')
    res = {'history': History.get_history(mode), 'mode': mode, 'title': title}
    clear_working_led()
    return JsonResponse(res)


def rate_ajax(request):
    """POST /ajax/rate

    :return: JSON status_str or error_str
    """
    filename = request.POST.get('filename')
    rating = request.POST.get('rating')
    return JsonResponse(Rating.set_rating(filename, int(rating)))


def download_ratings(request, mode='all'):
    """GET /download/ratings
    """
    raise_working_led()
    raise_sql_led()
    q = Rating.objects.filter(rating__gte=1)
    if mode == 'new':
        q = q.filter(original=False)
    clear_sql_led()
    data = serializers.serialize("xml", q)
    clear_working_led()
    response = HttpResponse(data, content_type="application/xml")
    response['Content-Disposition'] = 'attachment; filename=ratings.xml'
    return response


def download_history(request):
    """GET /download/history
    """
    raise_sql_led()
    raise_working_led()
    q = History.objects.all()
    clear_sql_led()
    data = serializers.serialize("xml", q)
    clear_working_led()
    response = HttpResponse(data, content_type="application/xml")
    response['Content-Disposition'] = 'attachment; filename=history.xml'
    return response


def download_playlist(request):
    """GET /download/playlist
    """
    source = request.GET.get('source')
    name = request.GET.get('name')
    raise_working_led()
    mpc = MPC()
    res = mpc.get_m3u(source, name)
    clear_working_led()
    return JsonResponse(res)


def download_smartpl(request, idx):
    """GET /download/smartpl
    """
    return JsonResponse(dict(data=[json.dumps(
        dict(object='piremote_smartplaylist',
             version=1,
             data=SmartPlaylist.get_json(idx)))]))


def upload_ratings(request):
    """/upload/ratings
    Handle file upload form.
    :return: upload page including status message about successful upload.
    """
    if request.method == 'POST':
        raise_working_led()
        form = UploadRatingsForm(request.POST, request.FILES)
        context = dict(title='Upload History File', text='History uploaded')

        if form.is_valid():
            raise_upload_led()
            filename = form.cleaned_data["ratingsfile"]
            data = request.FILES['ratingsfile'].read()
            parser = RatingsParser(filename, data)
            clear_upload_led()

            context['status_str'] = 'File parsed'
            context['errors'] = parser.errors
            context['parsed'] = parser.parsed_ratings
            context['unparsed'] = parser.not_parsed_ratings
            context['skipped'] = parser.skipped_ratings
        else:
            context['error_str'] = 'Uploaded file is not valid!'

        template = loader.get_template('piremote/upload_result.pug')
        clear_working_led()
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('piremote/upload_ratings.pug')
        return HttpResponse(template.render({}, request))


def upload_history(request):
    """/upload/history
    Handle file upload form.
    :return: upload page including status message about successful upload.
    """
    if request.method == 'POST':
        raise_working_led()
        form = UploadHistoryForm(request.POST, request.FILES)
        context = dict(title='Upload Ratings File', text='Ratings uploaded')

        if form.is_valid():
            raise_upload_led()
            filename = form.cleaned_data["historyfile"]
            data = request.FILES['historyfile'].read()
            parser = HistoryParser(filename, data)
            clear_upload_led()

            context['status_str'] = 'File parsed'
            context['errors'] = parser.errors
            context['parsed'] = parser.parsed_items
            context['unparsed'] = parser.not_parsed_items
            context['skipped'] = parser.skipped_items
        else:
            context['error_str'] = 'Uploaded file is not valid!'
        template = loader.get_template('piremote/upload_result.pug')
        clear_working_led()
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('piremote/upload_history.pug')
        return HttpResponse(template.render({}, request))


def smartpl_ajax(request, action):
    """POST /ajax/smartpl/ACTION"""
    raise_working_led()
    response = dict()
    if action == 'create':
        title = request.POST.get('name')
        if SmartPlaylist.has_smart_playlist(title):
            response['error_str'] = 'Smart playlist exists: {0}'.format(title)
        else:
            s = SmartPlaylist(title=title, description='')
            s.save()
            response['status_str'] = 'Smart playlist {0} generated.'.format(title)
            response['name'] = title
    elif action == 'rm':
        title = request.POST.get('name')
        idx = request.POST.get('id')
        SmartPlaylist.objects.filter(id=idx).delete()
        response['status_str'] = 'Deleted smart playlist with title {0}.'.format(title)
    elif action == 'rename':
        title = request.POST.get('name')
        idx = request.POST.get('id')
        SmartPlaylist.objects.filter(id=idx).update(title=title)
        response['status_str'] = 'Renamed smart playlist to {0}.'.format(title)
    elif action == 'clone':
        idx = request.POST.get('id')
        response['status_str'] = SmartPlaylist.clone(idx)
    else:
        response['error_str'] = 'Unknown action for smart playlist: {0}'.format(action)

    clear_working_led()
    return JsonResponse(response)


def smartplaction_ajax(request, id, action):
    """POST /ajax/smartplaction/ID/ACTION"""
    raise_working_led()
    response = dict(success=True)
    if action == 'new':
        SmartPlaylistItem.add_new(id)
        response['reload'] = True
    elif action == 'itemtype':
        new_type = int(request.POST.get('type'))
        SmartPlaylistItem.change_type(id, new_type)
        response['reload'] = True
    elif action == 'rmitem':
        SmartPlaylistItem.objects.filter(id=id).delete()
        response['reload'] = True
    elif action == 'downitem' or action == 'upitem':
        SmartPlaylistItem.move_item(id, action)
        response['reload'] = True
    elif action == 'setpayload':
        payload = request.POST.get('payload')
        SmartPlaylistItem.objects.filter(id=id).update(payload=payload)
    elif action == 'setweight':
        weight = float(request.POST.get('weight'))
        SmartPlaylistItem.objects.filter(id=id).update(weight=weight)
    elif action == 'negate':
        negate = request.POST.get('negate') == '1'
        SmartPlaylistItem.objects.filter(id=id).update(negate=negate)
    elif action == 'addpayload':
        payload = request.POST.get('payload')
        r = SmartPlaylistItem.add_payload(id, payload)
        response['reload'] = r
    elif action == 'setpayloads':
        payloads = request.POST.getlist('payloads[]', [])
        SmartPlaylistItem.set_payloads(id, payloads)
        response['reload'] = True
    elif action == 'rmpayload':
        payload = request.POST.get('payload')
        r = SmartPlaylistItem.rm_payload(id, payload)
        response['reload'] = r
    elif action == 'apply':
        count = int(request.POST.get('count'))
        playlist = request.POST.get('playlist', '')
        a = ApplySmartPlaylist(id, count)
        a.apply_filters(playlist)
        if a.error:
            response['error_str'] = a.result_string
        else:
            response['status_str'] = a.result_string
    else:
        response['success'] = False
        response['error_str'] = 'Unknown smart pl action {0}'.format(action)

    clear_working_led()
    return JsonResponse(response)
