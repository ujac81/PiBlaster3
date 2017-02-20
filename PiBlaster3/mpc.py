
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
            res = {'album': '', 'artist': '', 'title': 'Not Playing!'}
        return res

    def browse(self, path):
        """

        :param path:
        :return: Array of ['1', title, '', '', '', directory] for dirs
        """
        if path is None:
            return None

        self.ensure_connected()

        result = []

        try:
            lsdir = self.client.lsinfo(path)
        except CommandError:
            return None

        for item in lsdir:
            if 'directory' in item:
                title = os.path.basename(item['directory'])
                result.append(['1', title, '', '', '', item['directory']])
            # need to check for file item -- may not scan 'playlist' items.
            elif 'file' in item:
                res = ['2']
                if 'title' in item:
                    res.append(item['title'])
                else:
                    no_ext = os.path.splitext(item['file'])[0]
                    res.append(os.path.basename(no_ext).replace('_', ' '))

                res.append(item['artist'] if 'artist' in item else '')
                res.append(item['album'] if 'album' in item else '')
                length = time.strftime("%M:%S", time.gmtime(int(item['time'])))
                res.append(length)
                res.append(item['file'])
                result.append(res)

        return result








