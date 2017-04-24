"""mpc.py -- interface between AJAX request in views and MPDClient.

"""

from mpd import MPDClient, ConnectionError, CommandError
import os
import random
import re
import time

from django.conf import settings
from PiBlaster3.translate_genre import translate_genre, all_genres
from piremote.models import Rating


class MPC:
    """MPD Client for all actions in views.py.

    Connect to music player daemon and send/receive data.
    Connects on init, so no need to call reconnect() yourself.
    NOTE: some methods might throw, but this is not too bad for use in django, just reload page.
    """

    def __init__(self):
        """Create MPDClient and connect."""
        self.connected = False
        self.error = False
        self.client = MPDClient()
        self.client.timeout = 10
        self.reconnect()
        self.truncated = 0  # set to the truncate value if truncated (search, list, ...)

    def reconnect(self):
        """Try connect 5 times, if not successful self.connected will be False."""

        self.connected = False
        self.error = False

        try:
            self.client.disconnect()
        except ConnectionError:
            pass

        for i in range(5):
            try:
                self.client.connect('localhost', 6600)
                self.connected = True
            except ConnectionError:
                time.sleep(0.1)
                pass
            if self.connected:
                return True

        self.error = True
        return False

    def get_stats(self):
        """Displays statistics.

        :return: {
            artists: number of artists
            albums: number of albums
            songs: number of songs
            uptime: daemon uptime in seconds
            db_playtime: sum of all song times in the db
            db_update: last db update in UNIX time
            playtime: time length of music played
            free: bytes available in upload folder (if PB_UPLOAD_DIR set)}
        """
        self.ensure_connected()
        stats = self.client.stats()
        if settings.PB_UPLOAD_DIR is not None:
            s = os.statvfs(settings.PB_UPLOAD_DIR)
            free = s.f_bavail * s.f_frsize
            stats['free'] = free
        return stats

    def get_status(self):
        """Get status dict from mpd.
        If connection error occurred, try to reconnect max 5 times.

        :return: {'audio': '44100:24:2',
                 'bitrate': '320',
                 'consume': '0',
                 'elapsed': '10.203',
                 'mixrampdb': '0.000000',
                 'mixrampdelay': 'nan',
                 'nextsong': '55',
                 'nextsongid': '55',
                 'playlist': '2',
                 'playlistlength': '123',
                 'random': '1',
                 'repeat': '1',
                 'single': '0',
                 'song': '58',
                 'songid': '58',
                 'state': 'pause',
                 'time': '10:191',
                 'volume': '40',
                 'xfade': '0'}

        :return: MPDClient.status()
        """
        res = {'error_str': self.error}
        for i in range(5):
            try:
                res = self.client.status()
            except (ConnectionError, CommandError):
                self.reconnect()
                pass
        res['error_str'] = self.error
        return res

    def get_status_int(self, key, dflt=0):
        """Fetch value from mpd status dict as int,
        fallback to dflt if no such key.
        NOTE: Won't catch failed conversions.
        """
        stat = self.get_status()
        if key in stat:
            return int(stat[key])
        return dflt

    def ensure_connected(self):
        """Make sure we are connected."""
        # Abuse get_status() method which tries to connect up to 5 times.
        self.get_status()

    def get_currentsong(self):
        """Fetch current song dict from mpd.
        Force reconnect if failed.

        :return: {'album': 'Litany',
                 'albumartist': 'Vader',
                 'artist': 'Vader',
                 'date': '2000',
                 'file': 'local/Extreme_Metal/Vader - Litany - 01 - Wings.mp3',
                 'genre': 'Death Metal',
                 'id': '58',
                 'last-modified': '2014-12-10T20:00:58Z',
                 'pos': '58',
                 'time': '191',
                 'title': 'Wings',
                 'track': '1'}
        """
        self.ensure_connected()
        res = self.client.currentsong()
        if len(res) == 0:
            res = {'album': '', 'artist': '', 'title': 'Not Playing!', 'time': 0, 'file': ''}
        return res

    def get_status_data(self):
        """Combined currentsong / status data for AJAX GET or POST on index page

        :return: see generate_status_data()
        """
        status = self.get_status()
        current = self.get_currentsong()
        return self.generate_status_data(status, current)

    @staticmethod
    def generate_status_data(status, current):
        """Combined currentsong / status data

        :return: {title: xxx
                  time: seconds
                  album: xxx
                  artist: xxx
                  date: yyyy
                  id: N
                  elapsed: seconds
                  random: bool
                  repeat: bool
                  volume: percentage
                  state: ['playing', 'stopped', 'paused']
                  playlist: VERSION-NUMBER
                  playlistlength: N
                  file: local/Mp3/...../file.mp3
                  }
        """
        data = {}
        if len(current) == 0:
            current = {'album': '', 'artist': '', 'title': 'Not Playing!', 'time': 0, 'file': ''}
        if 'title' in current:
            data['title'] = current['title']
        else:
            no_ext = os.path.splitext(current['file'])[0]
            data['title'] = os.path.basename(no_ext).replace('_', ' ')
        data['time'] = current['time'] if 'time' in current else 0
        for key in ['album', 'artist', 'date', 'id', 'file']:
            data[key] = current[key] if key in current else ''
        for key in ['elapsed', 'random', 'repeat', 'volume', 'state', 'playlist', 'playlistlength']:
            data[key] = status[key] if key in status else '0'
        data['rating'] = Rating.get_rating(current['file'])
        return data

    def volume(self):
        """Current volume as int in [0,100]"""
        return self.get_status_int('volume')

    def change_volume(self, amount):
        """Add amount to current volume int [-100, +100]"""
        self.set_volume(self.volume() + amount)

    def set_volume(self, setvol):
        """Set current volume as int in [0,100]"""
        self.ensure_connected()
        vol = setvol
        if vol < 0:
            vol = 0
        if vol > 100:
            vol = 100
        try:
            self.client.setvol(vol)
        except CommandError:
            pass
        return self.volume()

    def update_database(self):
        """Trigger mpd update command (!= rescan).
        Idler will get notified when scan is done.
        """
        self.ensure_connected()
        self.client.update()

    def playlistinfo(self, start, end):
        """Get playlist items in interval [start, end)
        :param start: start index in playlist (start = 0)
        :param end: end index in playlist (excluded)
        :return: [[pos, title, artist, album, length, id, file, rating]]
        """

        pl_len = self.get_status_int('playlistlength')
        pl_ver = self.get_status_int('playlist')
        result = {'version': pl_ver, 'data': [], 'length': pl_len}

        if end == -1:
            end = pl_len

        if end < start:
            return result

        if start >= pl_len:
            return result

        items = self.client.playlistinfo("%d:%d" % (start, end))

        # make sure we only do 1 SQL query for all ratings.
        files = [x['file'] for x in items]
        q = Rating.objects.values('path', 'rating').filter(path__in=files)
        rat_d = dict([(x['path'], x['rating']) for x in q])

        data = []
        for item in items:
            file = item['file'] if 'file' in item else ''
            res = [item['pos']]
            if 'title' in item:
                res.append(item['title'])
            elif 'file' in item:
                no_ext = os.path.splitext(item['file'])[0]
                res.append(os.path.basename(no_ext).replace('_', ' '))
            res.append(item['artist'] if 'artist' in item else '')
            res.append(item['album'] if 'album' in item else '')
            length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
            res.append(length)
            res.append(item['id'])
            res.append(file)
            res.append(rat_d[file] if file in rat_d else 0)
            data.append(res)
        result['data'] = data
        return result

    def playlistinfo_by_name(self, plname):
        """Get condensed playlist info.

        Used for playlist edit mode.

        :param plname: name of playlist
        :return: [[file, artist - title, pos]]
        """
        self.ensure_connected()
        info = self.client.listplaylistinfo(plname)
        result = []
        pos = 0
        for item in info:
            res = ''
            if 'artist' in item:
                res += item['artist'] + ' - '
            if 'title' in item:
                res += item['title']
            else:
                no_ext = os.path.splitext(item['file'])[0]
                res = os.path.basename(no_ext).replace('_', ' ')
            result.append([item['file'], res, pos])
            pos += 1
        return result

    def playlistinfo_full(self, id):
        """Return full playlistinfo for song with id.

        :param id: song id from playlist
        :return: MPDClient.playlistid(id)
        """
        self.ensure_connected()
        return self.client.playlistid(id)

    def file_info(self, file):
        """Return full info for file.

        :param file
        :return: [{'last-modified': '2016-02-29T18:03:53Z',
            'time': '313',
            'album': 'Master Of Puppets',
            'artist': 'Metallica',
            'file': 'Mp3/M/......mp3',
            'title': 'Battery',
            'date': '1986',
            'track': '01/08',
            'albumartist': 'Metallica',
            'genre': 'Thrash Metal'}]
        """
        self.ensure_connected()
        res = self.client.find('file', file)
        for item in res:
            if 'genre' in item:
                m = re.match(r"^\((\d+)", item['genre'])
                if m:
                    item['genre'] = translate_genre(int(m.group(1)))
            item['rating'] = Rating.get_rating(item['file'])
        return res

    def playlist_changes(self, version):
        """Get changes in playlist since version.

        NOTE: if new playlist is shorter, use playlistlength to truncate old playlist view.

        :param version: diff version of playlist.
        :return: {version: new version
                  changes: [[pos, title, artist, album, length, id, file, rating]]
                  length: new playlist length}
        """
        pl_len = self.get_status_int('playlistlength')
        pl_ver = self.get_status_int('playlist')
        changes = self.client.plchanges(version)

        # make fast query for all ratings
        files = [x['file'] for x in changes]
        q = Rating.objects.values('path', 'rating').filter(path__in=files)
        rat_d = dict([(x['path'], x['rating']) for x in q])

        result = []
        for change in changes:
            file = item['file'] if 'file' in item else ''
            item = self.client.playlistinfo(change['pos'])[0]
            res = [item['pos']]
            if 'title' in item:
                res.append(item['title'])
            elif 'file' in item:
                no_ext = os.path.splitext(item['file'])[0]
                res.append(os.path.basename(no_ext).replace('_', ' '))
            res.append(item['artist'] if 'artist' in item else '')
            res.append(item['album'] if 'album' in item else '')
            length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
            res.append(length)
            res.append(item['id'])
            res.append(file)
            res.append(rat_d[file] if file in rat_d else 0)
            result.append(res)
        return {'version': pl_ver, 'changes': result, 'length': pl_len}

    def exec_command(self, cmd):
        """Execute command for music player daemon.

        :param cmd: ['back', 'playpause', 'stop', 'next', 'decvol', 'incvol', 'random', 'repeat', 'seekcur SEC']
        """
        success = True
        self.ensure_connected()
        try:
            if cmd == 'back':
                self.client.previous()
            elif cmd == 'playpause':
                status = self.get_status()
                if status['state'] == 'play':
                    self.client.pause()
                else:
                    self.client.play()
            elif cmd == 'stop':
                self.client.stop()
            elif cmd == 'next':
                self.client.next()
            elif cmd == 'decvol':
                self.change_volume(-3)
            elif cmd == 'incvol':
                self.change_volume(3)
            elif cmd == 'random':
                rand = self.get_status_int('random')
                self.client.random(1 if rand == 0 else 0)
            elif cmd == 'repeat':
                rep = self.get_status_int('repeat')
                self.client.repeat(1 if rep == 0 else 0)
            elif cmd.startswith('seekcur'):
                pct = float(cmd.split()[1])
                cur = self.get_currentsong()
                jump = 0.0
                if 'time' in cur:
                    jump = float(cur['time']) * pct / 100.0
                self.client.seekcur(jump)
            else:
                success = False
        except CommandError:
            success = False
            pass
        except ConnectionError:
            success = False
            pass

        data = self.get_status_data()
        data['cmd'] = cmd
        data['success'] = success
        return data

    def browse(self, path):
        """Browse files in files view.

        :param path: Directory to list.
        :return: Array of ['1', title, '', '', '', directory] for dirs
                 Array of ['2', title, artist, album, length, file, ext, date, rating] for audio files
        """
        if path is None:
            return None

        self.ensure_connected()

        result = []

        try:
            lsdir = self.client.lsinfo(path)
        except CommandError:
            return None

        # check if we have differing artists in directory
        mixed_artists = False
        last_artist = None
        for item in lsdir:
            if 'file' in item:
                if 'artist' in item:
                    if last_artist is None:
                        last_artist = item['artist']
                    elif last_artist != item['artist']:
                        mixed_artists = True
                        break

        # query all ratings at once
        files = [x['file'] for x in lsdir if 'file' in x]
        q = Rating.objects.values('path', 'rating').filter(path__in=files)
        rat_d = dict([(x['path'], x['rating']) for x in q])

        for item in lsdir:
            if 'directory' in item:
                title = os.path.basename(item['directory'])
                result.append(['1', title, '', '', '', item['directory']])
            # need to check for file item -- may not scan 'playlist' items.
            elif 'file' in item:
                res = ['2']
                if 'title' in item:
                    if mixed_artists and 'artist' in item:
                        res.append(item['artist'] + ' - ' + item['title'])
                    else:
                        res.append(item['title'])
                else:
                    no_ext = os.path.splitext(item['file'])[0]
                    res.append(os.path.basename(no_ext).replace('_', ' '))

                res.append(item['artist'] if 'artist' in item else '')
                res.append(item['album'] if 'album' in item else '')
                length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
                res.append(length)
                res.append(item['file'])

                # add extension as result for files --> matches image png in static/img
                ext = os.path.splitext(item['file'])[1][1:].lower()
                if ext not in ['mp3', 'wma', 'ogg', 'wav', 'flac', 'mp4']:
                    ext = 'audio'
                res.append(ext)
                res.append(item['date'] if 'date' in item else '')
                res.append(rat_d[item['file']] if item['file'] in rat_d else 0)

                result.append(res)

        return result

    def playlist_action(self, cmd, plname, items):
        """Perform action on playlist.

        :param cmd: ['append', 'insert', 'clear', 'deleteid(s)?', 'playid', 'playid(s)?next', 'moveid', 'moveid(s)?end'
        :param plname: playlist name -- '' for current playlist
        :param items: payload array for command
        :return: status string
        """

        self.ensure_connected()

        if (cmd == 'append') or (cmd == 'insert' and 'pos' not in self.get_currentsong()):
            # append at end if command is append or insert and not playing
            for item in items:
                try:
                    if len(plname):
                        self.client.playlistadd(plname, item)
                    else:
                        self.client.add(item)
                except CommandError:
                    return 'Add error'
                    pass
            return '%d' % len(items) + ' items appended to playlist ' + plname
        elif cmd == 'clear':
            # clear playlist
            try:
                self.client.clear()
            except CommandError:
                return 'Clear error'
                pass
            return 'Playlist cleared.'
        elif cmd == 'deleteid' or cmd == 'deleteids':
            # Remove items from playlist
            for i in sorted([int(x) for x in items], reverse=True):
                try:
                    self.client.deleteid(i)
                except CommandError:
                    return 'Delete error'
                    pass
            return '%d items removed from playlist' % len(items)
        elif cmd == 'insert':
            # insert (list of) song(s) after current song
            pos = int(self.get_currentsong()['pos'])+1
            for item in reversed(items):
                try:
                    self.client.addid(item, pos)
                except CommandError:
                    return 'Add error'
                    pass
            return '%d' % len(items) + ' items inserted into playlist ' + plname
        elif cmd == 'playid':
            # Play song with #id now.
            self.client.playid(int(items[0]))
            title = self.get_status_data()['title']
            return 'Playing ' + title
        elif cmd == 'playidnext':
            # Move song with #id after current song
            try:
                self.client.moveid(int(items[0]), -1)
            except CommandError:
                return 'Move error'
                pass
            return 'Moved 1 song after current song'
        elif cmd == 'playidsnext':
            # Move songs with [#id] after current song
            for item in reversed(items):
                try:
                    self.client.moveid(int(item), -1)
                except CommandError:
                    return 'Move error'
                    pass
            return 'Moved %d songs after current song' % len(items)
        elif cmd == 'moveid':
            # move song(s) with id(s) to end
            try:
                self.client.moveid(items[0], items[1])
            except CommandError:
                return 'Move error'
                pass
            return 'Moved song to position %d' % (int(items[1])+1)
        elif cmd == 'moveidend' or cmd == 'moveidsend':
            # move song(s) with id(s) to end
            move_to = self.get_status_int('playlistlength') - 1
            for i in [int(x) for x in items][::-1]:
                try:
                    self.client.moveid(i, move_to)
                except CommandError:
                    return 'Move error'
                    pass
            return 'Moved %d songs to end' % len(items)
        elif cmd == 'randomize':
            # clear playlist
            try:
                self.client.shuffle()
            except CommandError:
                return 'Shuffle error'
                pass
            return 'Playlist randomized.'
        elif cmd == 'randomize-rest':
            # clear playlist
            try:
                song_pos = self.get_status_int('song') + 1
                pl_len = self.get_status_int('playlistlength') - 1
                self.client.shuffle("%d:%d" % (song_pos, pl_len))
            except CommandError:
                return 'Shuffle error'
                pass
            return 'Playlist randomized after current song.'
        elif cmd == 'seed':
            n = int(items[0])
            random.seed()
            db_files = self.client.list('file')
            filter_dirs = items[1]
            if filter_dirs != '':
                db_files = [i for i in db_files if i.startswith(filter_dirs)]
            if len(db_files) == 0:
                return 'No items to seed in dir %s' % filter_dirs
            add = []
            for i in range(n):
                add.append(db_files[random.randrange(0, len(db_files))])
            return self.playlist_action('append', plname, add)

        return 'Unknown command '+cmd

    def search_file(self, arg, limit=500):
        """ Search in MPD data base using 'any' and 'file' tag.
        :param arg: search pattern
        :param limit: max amount of results
        :return: {status: '', error: '', result: [title, artist, album, length, '', filename]}
                    Dummy element added at position #4 to have filename at position #5
        """
        if arg is None or len(arg) < 3:
            return {'error_str': 'Search pattern must contain at least 3 characters!'}

        self.ensure_connected()

        result = []

        # Search for first word and filter results later.
        # MPD search does not support AND for multiple words.
        first_arg = arg.split(' ')[0]
        other_args = [s.lower() for s in arg.split(' ')[1:] if len(s)]

        try:
            search = self.client.search('any', first_arg)
            search += self.client.search('file', first_arg)
        except CommandError as e:
            return {'error_str': 'Command error in search: %s' % e}

        has_files = []

        self.truncated = 0
        if len(search) > limit:
            self.truncated = len(search) - limit

        # query all ratings at once
        files = sorted(set([x['file'] for x in search if 'file' in x]))
        q = Rating.objects.values('path', 'rating').filter(path__in=files)
        rat_d = dict([(x['path'], x['rating']) for x in q])

        for item in search[:limit]:
            if 'file' not in item:
                continue
            if item['file'] in has_files:
                continue

            has_files.append(item['file'])

            # Filter for remaining args.
            if len(other_args):
                # Generate string of all values in search item to check for search terms.
                match_list = [value for key, value in item.items()]
                try:
                    match = ''.join(match_list).lower()
                except TypeError:
                    # There are arrays inside the results.... Bad thing!
                    match_list = [i for sublist in match_list for i in sublist]
                    match = ''.join(match_list).lower()

                # Check remaining patterns
                valid = True
                for check in other_args:
                    if check not in match:
                        valid = False
                if not valid:
                    continue

            res = []
            if 'title' in item:
                res.append(item['title'])
            else:
                no_ext = os.path.splitext(item['file'])[0]
                res.append(os.path.basename(no_ext).replace('_', ' '))
            res.append(item['artist'] if 'artist' in item else '')
            res.append(item['album'] if 'album' in item else '')
            length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
            res.append(length)
            res.append('')  # dummy to push file to pos #5
            res.append(item['file'])
            res.append(rat_d[item['file']] if item['file'] in rat_d else 0)
            result.append(res)

        trunc_str = '(truncated)' if self.truncated else ''
        return {'status_str': '%d items found %s' % (len(result), trunc_str),
                'search': result,
                'truncated': self.truncated}

    def playlists_action(self, cmd, plname, payload):
        """Perform actions on list of playlists.

        :param cmd: [clear, delete, list, moveend, new, load,rename, saveas]
        :param plname: name of playlist
        :param payload: array of payload data for command
        :return: dict including error or status message.
        """
        self.ensure_connected()
        if cmd == 'clear':
            self.client.playlistclear(plname)
            return {'status_str': 'Playlist %s cleared' % plname}
        if cmd == 'delete':
            positions = sorted([int(i) for i in payload], reverse=True)
            for pos in positions:
                self.client.playlistdelete(plname, pos)
            return {'status_str': '%d items removed from playlist %s' % (len(positions), plname)}
        if cmd == 'list':
            pls = sorted([i['playlist'] for i in self.client.listplaylists() if 'playlist' in i])
            return {'pls': pls}
        if cmd == 'moveend':
            pl_len = len(self.client.listplaylist(plname))
            positions = sorted([int(i) for i in payload], reverse=True)
            for pos in positions:
                self.client.playlistmove(plname, pos, pl_len-1)
            return {'status_str': '%d items moved to end in playlist %s' % (len(positions), plname)}
        if cmd == 'new':
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s exists' % plname, 'plname': ''}
            self.client.save(plname)
            self.client.playlistclear(plname)
            return {'status_str': 'Playlist %s created' % plname, 'plname': plname}
        if cmd == 'load':
            self.client.load(plname)
            return {'status_str': 'Playlist %s added to playlist' % plname}
        if cmd == 'rename':
            plname_old = payload[0]
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s already exists.' % plname}
            self.client.rename(plname_old, plname)
            return {'status_str': 'Playlist %s renamed to %s' % (plname_old, plname)}
        if cmd == 'rm':
            self.client.rm(plname)
            return {'status_str': 'Playlist %s removed' % plname}
        if cmd == 'saveas':
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s already exists.' % plname}
            self.client.save(plname)
            return {'status_str': 'Current playlist saved to %s.' % plname}

        return {'error_str': 'No such command: %s' % cmd}

    def list_by(self, what, in_ratings, in_dates, in_genres, in_artists, in_albums, file_mode=False):
        """Create content data for browse view.

        :param what: category of results [date, genre, artist, album, song]
        :param in_ratings: list of ratings for filter ['All'] for all ratings
        :param in_dates: list of dates for filter ['All'] for all dates
        :param in_genres: list of genres for filter ['All'] for all
        :param in_artists: list of artists for filter ['All'] for all
        :param in_albums: list of albums for filter ['All'] for all
        :param file_mode: return result as file-list (required for seed_by())

        :return: List of results for browse view for next category:
                if what == 'genre' results will be artists and so on.
        """
        self.ensure_connected()

        seek = 'file' if file_mode or what == 'song' else what

        ratings_avail = {'All': [0, 1, 2, 3, 4, 5],
                         '5': [5],
                         'at least 4': [4, 5],
                         'at least 3': [3, 4, 5],
                         'at least 2': [2, 3, 4, 5],
                         'at least 1': [1, 2, 3, 4, 5],
                         'exactly 4': [4],
                         'exactly 3': [3],
                         'exactly 2': [2],
                         'exactly 1': [1],
                         'unrated': [0]
                         }

        if what == 'rating':
            if seek != 'file':
                return ['All', '5', 'at least 4', 'at least 3', 'at least 2', 'at least 1',
                        'exactly 4', 'exactly 3', 'exactly 2', 'exactly 1', 'unrated']
            else:
                return self.client.list(seek)

        # unroll ratings
        ratings = []
        if len(in_ratings) > 0 and in_ratings[0] != 'All':
            for rating in in_ratings:
                ratings += ratings_avail[rating]
            ratings = sorted(set(ratings))

        # Unroll special dates (decades like '1971-1980' or '2010-today')
        dates = []
        if len(in_dates) > 0 and in_dates[0] != 'All':
            for date in in_dates:
                if '-' in date:
                    m = re.match(r'(\d+)-(\d+)', date.replace('today', '2020'))
                    if m:
                        for y in range(int(m.group(1)), int(m.group(2)) + 1):
                            dates.append(y)
                else:
                    dates.append(int(date))

        q = Rating.objects.all().order_by('path')
        if len(ratings) > 0:
            q = q.filter(rating__in=ratings)
        if what in ['genre', 'artist', 'album', 'song'] and len(dates) > 0:
            q = q.filter(date__in=dates)
        if what in ['artist', 'album', 'song'] and len(in_genres) > 0 and in_genres[0] != 'All':
            q = q.filter(genre__in=in_genres)
        if what in ['album', 'song'] and len(in_artists) > 0 and in_artists[0] != 'All':
            q = q.filter(artist__in=in_artists)
        if what in ['song'] and len(in_albums) > 0 and in_albums[0] != 'All':
            q = q.filter(album__in=in_albums)

        if file_mode:
            return [x.path for x in q]
        if what == 'date':
            return sorted(set([x.date for x in q]))
        if what == 'genre':
            return sorted(set([x.genre for x in q]))
        if what == 'artist':
            return sorted(set([x.artist for x in q]))
        if what == 'album':
            return sorted(set([x.album for x in q]))
        if what == 'song':
            res = []
            for x in q:
                if x.artist != '':
                    res.append([x.path, x.artist + ' - ' + x.title, x.rating])
                else:
                    res.append([x.path, x.title, x.rating])
            return res

    def seed_by(self, count, plname, what, ratings, dates, genres, artists, albums):
        """Random add items to playlist from browse view.

        :param count: number of items to add
        :param plname: playlist name ('' for current)
        :param what: [date, genre, artist, album, song]
        :param ratings: see list_by()
        :param dates: see list_by()
        :param genres: see list_by()
        :param artists: see list_by()
        :param albums: see list_by()
        :return: status string.
        """

        files = self.list_by(what, ratings, dates, genres, artists, albums, file_mode=True)

        if len(files) == 0:
            return 'Zero results, nothing added.'

        if len(files) < count:
            return self.playlist_action('append', plname, files)

        random.seed()
        add = []
        for i in range(count):
            add.append(files[random.randrange(0, len(files))])

        return self.playlist_action('append', plname, add)
