"""mpc.py -- interface between AJAX request in views and MPDClient.

"""

from mpd import MPDClient, ConnectionError, CommandError, ProtocolError
import os
import random
import re
import time

from django.db.models import Q
from django.conf import settings
from PiBlaster3.translate_genre import translate_genre, all_genres
from .helpers import *
from piremote.models import Rating, History


class MPC:
    """MPD Client for all actions in views.py.

    Connect to music player daemon and send/receive data.
    Connects on init, so no need to call reconnect() yourself.
    NOTE: some methods might throw, but this is not too bad for use in django, just reload page.
    """

    def __init__(self):
        """Create MPDClient and connect."""
        logger = PbLogger('PROFILE MPD')
        self.connected = False
        self.error = False
        self.client = MPDClient()
        self.client.timeout = 10
        self.reconnect()
        self.truncated = 0  # set to the truncate value if truncated (search, list, ...)
        logger.print('__init__')

    def __del__(self):
        """Disconect if deleted by middleware and print debug"""
        print_debug('MPD DEL')

    def reconnect(self):
        """Try connect 5 times, if not successful self.connected will be False."""

        logger = PbLogger('PROFILE MPD')
        self.connected = False
        self.error = False

        try:
            self.client.disconnect()
        except (ConnectionError, BrokenPipeError, ValueError):
            pass

        for i in range(5):
            try:
                self.client.connect('localhost', 6600)
                self.connected = True
            except (ConnectionError, BrokenPipeError, ValueError):
                time.sleep(0.1)
            if self.connected:
                logger.print('reconnect()')
                return True

        self.error = True
        logger.print('reconnect() [FAIL!]')
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
            except (ConnectionError, CommandError, ProtocolError, BrokenPipeError, ValueError):
                print_debug('MPD RECONNECT')
                self.reconnect()
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
        data['title'] = save_item(current, 'title')
        data['time'] = current['time'] if 'time' in current else 0
        for key in ['album', 'artist', 'date', 'id', 'file']:
            data[key] = save_item(current, key)
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
        :return: {version=N, length=N, data=[[pos, title, artist, album, length, id, file, rating]]}
        """

        logger = PbLogger('PROFILE MPD')

        pl_len = self.get_status_int('playlistlength')
        pl_ver = self.get_status_int('playlist')
        result = {'version': pl_ver, 'data': [], 'length': pl_len}

        if end == -1:
            end = pl_len

        if end < start:
            return result

        if start >= pl_len:
            return result

        raise_mpd_led()

        items = self.client.playlistinfo("%d:%d" % (start, end))

        logger.print_step('items')

        # make sure we only do 1 SQL query for all ratings.
        raise_sql_led()
        files = [x['file'] for x in items]
        q = Rating.objects.filter(Q(path__in=files)).values('path', 'rating').all()
        rat_d = dict([(x['path'], x['rating']) for x in q])
        logger.print_step('sql')
        clear_sql_led()

        data = []
        for item in items:
            file = item['file'] if 'file' in item else ''
            res = list([item['pos']])
            res.append(save_title(item))
            res.append(save_item(item, 'artist'))
            res.append(save_item(item, 'album'))
            length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
            res.append(length)
            res.append(item['id'])
            res.append(file)
            res.append(rat_d[file] if file in rat_d else 0)
            data.append(res)
        result['data'] = data
        clear_mpd_led()
        logger.print('playlistinfo() done.')
        return result

    def playlistinfo_by_name(self, plname):
        """Get condensed playlist info.

        Used for playlist edit mode.

        :param plname: name of playlist
        :return: [[file, artist - title, pos]]
        """
        self.ensure_connected()
        try:
            info = self.client.listplaylistinfo(plname)
        except CommandError:
            return []  # no such playlist
        result = []
        pos = 0
        for item in info:
            title = save_artist_title(item)
            result.append([item['file'], title, pos])
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
                m = re.match(r"^\((\d+)", save_item(item, 'genre'))
                if m:
                    item['genre'] = translate_genre(int(m.group(1)))
            item['rating'] = Rating.get_rating(item['file'])
            for check in ['title', 'artist', 'album']:
                item[check] = save_item(item, check)
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
        q = Rating.objects.filter(Q(path__in=files)).values('path', 'rating').all()
        rat_d = dict([(x['path'], x['rating']) for x in q])

        result = []
        for change in changes:
            item = self.client.playlistinfo(change['pos'])[0]
            file = item['file'] if 'file' in item else ''
            res = list([item['pos']])
            res.append(save_title(item))
            res.append(save_item(item, 'artist'))
            res.append(save_item(item, 'album'))
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
                flash_mpd_led()
                self.client.previous()
            elif cmd == 'playpause':
                flash_mpd_led()
                status = self.get_status()
                if status['state'] == 'play':
                    self.client.pause()
                else:
                    self.client.play()
            elif cmd == 'stop':
                flash_mpd_led()
                self.client.stop()
            elif cmd == 'next':
                flash_mpd_led()
                self.client.next()
            elif cmd == 'decvol':
                flash_mpd_led()
                self.change_volume(-3)
            elif cmd == 'incvol':
                flash_mpd_led()
                self.change_volume(3)
            elif cmd == 'random':
                flash_mpd_led()
                rand = self.get_status_int('random')
                self.client.random(1 if rand == 0 else 0)
            elif cmd == 'repeat':
                flash_mpd_led()
                rep = self.get_status_int('repeat')
                self.client.repeat(1 if rep == 0 else 0)
            elif cmd.startswith('seekcur'):
                flash_mpd_led()
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
        except ConnectionError:
            success = False

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
        logger = PbLogger('PROFILE MPD')

        if path is None:
            return None

        self.ensure_connected()

        result = []

        raise_mpd_led()

        try:
            lsdir = self.client.lsinfo(path)
        except CommandError:
            clear_mpd_led()
            return None

        # check if we have differing artists in directory
        mixed_artists = False
        last_artist = None
        for item in lsdir:
            if 'file' in item:
                if 'artist' in item:
                    if last_artist is None:
                        last_artist = save_item(item, 'artist')
                    elif last_artist != save_item(item, 'artist'):
                        mixed_artists = True
                        break

        logger.print_step('browse mpd done')

        # query all ratings at once
        raise_sql_led()
        files = [x['file'] for x in lsdir if 'file' in x]
        q = Rating.objects.filter(Q(path__in=files)).values('path', 'rating').all()
        rat_d = dict([(x['path'], x['rating']) for x in q])
        clear_sql_led()

        logger.print_step('browse sql done')

        for item in lsdir:
            if 'directory' in item:
                title = os.path.basename(item['directory'])
                result.append(['1', title, '', '', '', item['directory']])
            # need to check for file item -- may not scan 'playlist' items.
            elif 'file' in item:
                res = ['2']
                if 'title' in item:
                    if mixed_artists and 'artist' in item:
                        res.append(save_artist_title(item))
                    else:
                        res.append(save_title(item))
                else:
                    no_ext = os.path.splitext(item['file'])[0]
                    res.append(os.path.basename(no_ext).replace('_', ' '))

                res.append(save_item(item, 'artist'))
                res.append(save_item(item, 'album'))
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

        clear_mpd_led()
        logger.print('browse() done')
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
            raise_mpd_led()
            for item in items:
                try:
                    if len(plname):
                        self.client.playlistadd(plname, item)
                    else:
                        self.client.add(item)
                except CommandError:
                    clear_mpd_led()
                    return 'Add error'
            clear_mpd_led()
            return '%d' % len(items) + ' items appended to playlist ' + plname
        elif cmd == 'clear':
            # clear playlist
            try:
                self.client.clear()
            except CommandError:
                return 'Clear error'
            flash_mpd_led()
            return 'Playlist cleared.'
        elif cmd == 'deleteallbutcur':
            flash_mpd_led()
            now_pos = self.get_status_int('song', -1)
            now_len = self.get_status_int('playlistlength', -1)
            if now_pos == -1:
                self.client.clear()
            else:
                self.client.delete((0, now_pos))
                self.client.delete((1,))
            new_len = self.get_status_int('playlistlength', -1)
            clear_mpd_led()
            return 'Deleted {} items from playlist.'.format(now_len-new_len)
        elif cmd == 'deleteid' or cmd == 'deleteids':
            # Remove items from playlist
            for i in sorted([int(x) for x in items], reverse=True):
                try:
                    self.client.deleteid(i)
                except CommandError:
                    return 'Delete error'
            flash_mpd_led()
            return '%d items removed from playlist' % len(items)
        elif cmd == 'insert':
            # insert (list of) song(s) after current song
            pos = int(self.get_currentsong()['pos'])+1
            for item in reversed(items):
                try:
                    self.client.addid(item, pos)
                except CommandError:
                    return 'Add error'
            flash_mpd_led()
            return '%d' % len(items) + ' items inserted into playlist ' + plname
        elif cmd == 'playid':
            # Play song with #id now.
            self.client.playid(int(items[0]))
            title = self.get_status_data()['title']
            flash_mpd_led()
            return 'Playing ' + title
        elif cmd == 'playidnext':
            # Move song with #id after current song
            try:
                self.client.moveid(int(items[0]), -1)
            except CommandError:
                return 'Move error'
            flash_mpd_led()
            return 'Moved 1 song after current song'
        elif cmd == 'playidsnext':
            # Move songs with [#id] after current song
            for item in reversed(items):
                try:
                    self.client.moveid(int(item), -1)
                except CommandError:
                    return 'Move error'
            flash_mpd_led()
            return 'Moved %d songs after current song' % len(items)
        elif cmd == 'moveid':
            # move song(s) with id(s) to end
            try:
                self.client.moveid(items[0], items[1])
            except CommandError:
                return 'Move error'
            flash_mpd_led()
            return 'Moved song to position %d' % (int(items[1])+1)
        elif cmd == 'moveidend' or cmd == 'moveidsend':
            # move song(s) with id(s) to end
            move_to = self.get_status_int('playlistlength') - 1
            for i in [int(x) for x in items][::-1]:
                try:
                    self.client.moveid(i, move_to)
                except CommandError:
                    return 'Move error'
            flash_mpd_led()
            return 'Moved %d songs to end' % len(items)
        elif cmd == 'randomize':
            # clear playlist
            try:
                self.client.shuffle()
            except CommandError:
                return 'Shuffle error'
            flash_mpd_led()
            return 'Playlist randomized.'
        elif cmd == 'randomize-rest':
            # clear playlist
            try:
                song_pos = self.get_status_int('song') + 1
                pl_len = self.get_status_int('playlistlength') - 1
                self.client.shuffle("%d:%d" % (song_pos, pl_len))
            except CommandError:
                return 'Shuffle error'
            flash_mpd_led()
            return 'Playlist randomized after current song.'
        elif cmd == 'seed':
            raise_mpd_led()
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
            clear_mpd_led()
            return self.playlist_action('append', plname, add)

        return 'Unknown command '+cmd

    def search_file(self, arg, limit=500):
        """ Search in MPD data base using 'any' and 'file' tag.
        :param arg: search pattern
        :param limit: max amount of results
        :return: {status: '', error: '', result: [title, artist, album, length, '', filename, rating]}
                    Dummy element added at position #4 to have filename at position #5
        """
        logger = PbLogger('PROFILE MPD')
        if arg is None or len(arg) < 3:
            return {'error_str': 'Search pattern must contain at least 3 characters!'}

        self.ensure_connected()

        result = []

        # Search for first word and filter results later.
        # MPD search does not support AND for multiple words.
        first_arg = arg.split(' ')[0]
        other_args = [s.lower() for s in arg.split(' ')[1:] if len(s)]

        try:
            raise_mpd_led()
            search = self.client.search('any', first_arg)
            search += self.client.search('file', first_arg)
            clear_mpd_led()
        except CommandError as e:
            return {'error_str': 'Command error in search: %s' % e}

        logger.print_step('search init done.')

        has_files = []
        for item in search:
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
            res.append(save_title(item))
            res.append(save_item(item, 'artist'))
            res.append(save_item(item, 'album'))
            length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
            res.append(length)
            res.append('')  # dummy to push file to pos #5
            res.append(item['file'])
            res.append(0)  # ratings placeholder
            result.append(res)

        logger.print_step('search items filtered.')

        # truncate to N results
        trunc_res = result[:limit]
        self.truncated = 0
        if len(result) > limit:
            self.truncated = len(result) - limit
        trunc_str = '(truncated)' if self.truncated else ''

        # query all ratings at once
        raise_sql_led()
        files = sorted(set([x[5] for x in trunc_res]))
        q = Rating.objects.filter(Q(path__in=files)).values('path', 'rating').all()
        rat_d = dict([(x['path'], x['rating']) for x in q])
        clear_sql_led()
        for item in trunc_res:
            item[6] = rat_d[item[5]] if item[5] in rat_d else 0

        logger.print_step('search SQL done.')
        logger.print('search() done.')

        return {'status_str': '%d items found %s' % (len(result), trunc_str),
                'search': trunc_res,
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
            flash_mpd_led()
            return {'status_str': 'Playlist %s cleared' % plname}
        if cmd == 'delete':
            positions = sorted([int(i) for i in payload], reverse=True)
            for pos in positions:
                self.client.playlistdelete(plname, pos)
            flash_mpd_led()
            return {'status_str': '%d items removed from playlist %s' % (len(positions), plname)}
        if cmd == 'list':
            pls = sorted([i['playlist'] for i in self.client.listplaylists() if 'playlist' in i])
            return {'pls': pls}
        if cmd == 'moveend':
            pl_len = len(self.client.listplaylist(plname))
            positions = sorted([int(i) for i in payload], reverse=True)
            for pos in positions:
                self.client.playlistmove(plname, pos, pl_len-1)
            flash_mpd_led()
            return {'status_str': '%d items moved to end in playlist %s' % (len(positions), plname)}
        if cmd == 'new':
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s exists' % plname, 'plname': ''}
            self.client.save(plname)
            self.client.playlistclear(plname)
            flash_mpd_led()
            return {'status_str': 'Playlist %s created' % plname, 'plname': plname}
        if cmd == 'load':
            self.client.load(plname)
            flash_mpd_led()
            return {'status_str': 'Playlist %s added to playlist' % plname}
        if cmd == 'rename':
            plname_old = payload[0]
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s already exists.' % plname}
            self.client.rename(plname_old, plname)
            flash_mpd_led()
            return {'status_str': 'Playlist %s renamed to %s' % (plname_old, plname)}
        if cmd == 'rm':
            self.client.rm(plname)
            flash_mpd_led()
            return {'status_str': 'Playlist %s removed' % plname}
        if cmd == 'saveas':
            if plname in [i['playlist'] for i in self.client.listplaylists() if 'playlist' in i]:
                return {'error_str': 'Playlist %s already exists.' % plname}
            self.client.save(plname)
            flash_mpd_led()
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
        logger = PbLogger('PROFILE MPD')
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

        raise_sql_led()
        q = Rating.objects.all().order_by('path')
        logger.print_step('list_by: SQL select all')
        if len(ratings) > 0:
            q = q.filter(rating__in=ratings)
            logger.print_step('list_by: ratings filtered')
        if what in ['genre', 'artist', 'album', 'song'] and len(dates) > 0:
            q = q.filter(date__in=dates)
            logger.print_step('list_by: dates filtered')
        if what in ['artist', 'album', 'song'] and len(in_genres) > 0 and in_genres[0] != 'All':
            q = q.filter(genre__in=in_genres)
            logger.print_step('list_by: genres filtered')
        if what in ['album', 'song'] and len(in_artists) > 0 and in_artists[0] != 'All':
            q = q.filter(artist__in=in_artists)
            logger.print_step('list_by: artists filtered')
        if what in ['song'] and len(in_albums) > 0 and in_albums[0] != 'All':
            q = q.filter(album__in=in_albums)
            logger.print_step('list_by: albums filtered')
        clear_sql_led()

        res = []
        if file_mode:
            res = [x.path for x in q]
        if what == 'date':
            q2 = q.order_by('date').distinct('date')
            res = [x.date for x in q2]
        if what == 'genre':
            q2 = q.order_by('genre').distinct('genre')
            res = [x.genre for x in q2]
        if what == 'artist':
            q2 = q.order_by('artist').distinct('artist')
            res = [x.artist for x in q2]
        if what == 'album':
            q2 = q.order_by('album').distinct('album')
            res = [x.album for x in q2]
        if what == 'song':
            for x in q:
                if x.artist != '':
                    res.append([x.path, x.artist + ' - ' + x.title, x.rating])
                else:
                    res.append([x.path, x.title, x.rating])

        logger.print('list_by() done.')
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

    def get_m3u(self, source, name):
        """Return list uris to save as m3u file
        
        :param source: one of [current, saved, history]
        :param name: name of saved playlist or date for history
        :return: ['/path/to/mp31.mp3', '/path/to/next.ogg', ...]
        """
        res = []
        client = MPDClient()
        client.timeout = 10
        try:
            client.connect(settings.PB_MPD_SOCKET, 0)
            path_prefix = client.config()
        except ConnectionError:
            print("ERROR: CONNECT SOCKET")
            return dict(error_str='Failed to connect to MPD socket!', data=[])
        except CommandError:
            print("ERROR: COMMAND SOCKET")
            return dict(error_str='Failed to connect to MPD socket!', data=[])

        self.ensure_connected()
        if source == 'current':
            items = self.client.playlistinfo()
            res = [os.path.join(path_prefix, x['file']) for x in items]
        elif source == 'saved':
            try:
                items = self.client.listplaylistinfo(name)
                res = [os.path.join(path_prefix, x['file']) for x in items]
            except CommandError:
                return dict(error_str='Playlist not found: '+name, data=[])
        elif source == 'history':
            items = History.get_history(name)
            res = [os.path.join(path_prefix, x[5]) for x in items]

        return dict(status_str='Downloading %s playlist with %d items' % (source, len(res)),
                    data=res, prefix=path_prefix)
