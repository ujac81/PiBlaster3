"""upload_smart_playlist.py -- handle incomming json files with filter instructions 
"""

import datetime
import json

from piremote.models import SmartPlaylist, SmartPlaylistItem, SmartPlaylistItemPayload


class SmartPlaylistUploader:
    """Upload helper for downloaded smart playlist descriptions."""

    def __init__(self):
        pass

    def upload(self, playlist, name, f):
        """Takes json string from upload form and creates new smart playlist from it.
        
        :param playlist: name of new smart playlist
        :param name: filename of uploaded file
        :param f: binary stream of upload
        :return: {error_str='...'} or {status_str='....'}
        """
        json_str = ''
        for chunk in f.chunks():
            print(chunk)
            json_str += chunk.decode('utf-8')

        json_in = json.loads(json_str)

        if SmartPlaylist.has_smart_playlist(playlist):
            return dict(error_str='Smart playlist with name {} exists! Not uploading.'.format(playlist))

        if 'object' not in json_in or 'version' not in json_in or 'data' not in json_in:
            return dict(error_str='The uploaded file is not a PiRemote smart playlist file!')

        if json_in['object'] != 'piremote_smartplaylist' or json_in['version'] != 1:
            return dict(error_str='The uploaded file is not a PiRemote smart playlist file!')

        data = json_in['data']
        if 'description' not in data or 'time' not in data or 'items' not in data:
            return dict(error_str='The uploaded file is not a PiRemote smart playlist file!')

        t = datetime.datetime.strptime(data['time'], '%Y-%m-%d %H:%M')
        s = SmartPlaylist(title=playlist, description=data['description'], time=t)
        s.save()

        for item in data['items']:
            i = SmartPlaylistItem(playlist=s,
                                  itemtype=item[0],
                                  weight=item[1],
                                  payload=item[2],
                                  negate=item[3],
                                  position=item[4])
            i.save()
            for payload in item[6]:
                p = SmartPlaylistItemPayload(parent=i, item=payload)
                p.save()

        return dict(status_str='Smart playlist {0} generated from file {1}'.format(playlist, name))
