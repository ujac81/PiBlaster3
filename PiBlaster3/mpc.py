
from mpd import MPDClient, ConnectionError, CommandError
import os
import time


class MPC:

    def __init__(self):
        """

        """
        self.connected = False
        self.error = False
        self.client = MPDClient()
        self.client.timeout = 10
        self.reconnect()

    def reconnect(self):
        """

        :return:
        """

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

        :return:
        """
        res = {'error': self.error}
        for i in range(5):
            try:
                res = self.client.status()
            except (ConnectionError, CommandError):
                self.reconnect()
                pass
        res['error'] = self.error
        return res

    def get_status_int(self, key, dflt=0):
        """Fetch value from mpd status dict as int,
        fallback to dflt if no such key.
        Won't catch failed conversions.
        """
        stat = self.get_status()
        if key in stat:
            return int(stat[key])
        return dflt

    def ensure_connected(self):
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

        :return:
        """
        status = self.get_status()
        current = self.get_currentsong()
        data = {}
        data['title'] = current['title'] if 'title' in current else current['file']
        data['time'] = current['time'] if 'time' in current else 0
        for key in ['album', 'artist', 'date', 'id']:
            data[key] = current[key] if key in current else ''
        for key in ['elapsed', 'random', 'repeat', 'volume', 'state', 'playlist', 'playlistlength']:
            data[key] = status[key] if key in status else '0'
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
        self.client.setvol(vol)
        return self.volume()

    def playlistinfo(self, start, end):
        """Get playlist items in interval [start, end)
        :param start: start index in playlist (start = 0)
        :param end: end index in playlist (excluded)
        :return: [[pos, title, artist, album, length, id]]
        """

        pl_len = self.get_status_int('playlistlength')
        pl_ver = self.get_status_int('playlist')

        if end == -1:
            end = pl_len

        if end < start:
            return []

        if start >= pl_len:
            return []

        result = []
        items = self.client.playlistinfo("%d:%d" % (start, end))
        for item in items:
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
            result.append(res)

        return {'version': pl_ver, 'data': result}

    def exex_command(self, cmd):
        """

        :param cmd:
        :return:
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
        """

        :param path:
        :return: Array of ['1', title, '', '', '', directory] for dirs
                 Array of ['2', title, artist, album, length, file, ext, date] for audio files
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

                result.append(res)

        return result

    def playlist_action(self, cmd, plname, items):
        """

        :param cmd:
        :param plname:
        :param items:
        :return:
        """

        self.ensure_connected()

        if (cmd == 'append') or (cmd == 'insert' and 'pos' not in self.get_currentsong()):
            # append at end if command is append or insert and not playing
            for item in items:
                print("Append: "+item)
                try:
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

        return 'Unknown command '+cmd







