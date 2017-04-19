"""partymode.py -- threaded actions on playlist (like party mode)."""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PiBlaster3.settings")

from mpd import MPDClient, ConnectionError, CommandError
import datetime
import json
import sqlite3
import random
import threading
from time import sleep
from PiBlaster3.settings import *
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage


class MPC_Idler:
    """Keeps idle mode loop and party mode actions."""

    def __init__(self, main):
        self.main = main
        self.client = MPDClient()
        self.client.timeout = 10
        self.connected = False
        self.last_file = None
        random.seed()

    def reconnect(self):
        """Try to connect 5 times."""
        try:
            self.client.disconnect()
        except ConnectionError:
            pass

        self.connected = False
        for i in range(5):
            try:
                self.client.connect('localhost', 6600)
                self.connected = True
                return True
            except ConnectionError:
                sleep(0.1)
                pass
        return self.connected

    def ensure_connected(self):
        """make sure we are connected"""
        for i in range(5):
            try:
                self.client.status()
            except (ConnectionError, CommandError):
                self.reconnect()
                pass

    def check_party_mode(self, res, force=False):
        """Check if party mode is on, append items to playlist/shrink playlist if needed.

        Fetch settings directly from sqlite3 database of piremote App.
        This is some of the dirtiest hacks possible for process communication,
        but works for this purpose.

        DB settings:
        party_mode: ['0', '1'] '1' if use party mode -> auto extend playlist
        party_remain: 'int' number of songs to keep in playlist above current song.
        party_low_water: 'int' if this number of songs left, append.
        party_high_water: 'int' when appending, append until this number of songs left.
        """

        playlist_event = force
        for ev in res:
            if ev == 'player' or ev == 'playlist':
                playlist_event = True

        if not playlist_event:
            return

        # Fetch from database.
        # Note: this is how IPC is performed here -- not nice, but works.
        party_mode = False
        party_low_water = 10
        party_high_water = 20
        party_remain = 10

        db = DATABASES['default']
        conn = sqlite3.connect(database=db['NAME'], timeout=15)
        cur = conn.cursor()
        cur.execute('''SELECT key, value FROM piremote_setting''')
        for row in cur.fetchall():
            if row[0] == 'party_mode':
                party_mode = row[1] == '1'
            if row[0] == 'party_remain':
                party_remain = int(row[1])
            if row[0] == 'party_low_water':
                party_low_water = int(row[1])
            if row[0] == 'party_high_water':
                party_high_water = int(row[1])
        cur.close()
        conn.close()

        if not party_mode:
            return

        status = self.client.status()

        pos = int(status['song']) if 'song' in status else 0
        pl_len = int(status['playlistlength'])
        pl_remain = max(pl_len - pos - 1, 0)

        # Append randomly until high_water mark reached, if below low water mark.
        if pl_remain < party_low_water:
            pl_add = max(party_high_water - pl_remain, 0)
            db_files = self.client.list('file')
            for i in range(pl_add):
                self.client.add(db_files[random.randrange(0, len(db_files))])

        # Shrink playlist until 'remain' songs left before current item.
        if pos > party_remain:
            for i in range(pos - party_remain):
                self.client.delete(0)

    def mpc_idle(self):
        """Idle until event received from MPD.
        Note: this is blocking. To break this loop, toggle some switch on MPD.
        """
        self.ensure_connected()
        res = ['']
        if self.connected:
            res = self.client.idle()
            self.check_party_mode(res)

        if 'update' in res and 'updating_db' not in self.client.status():
            # let ratings scanner do rescan if database updated
            self.main.rescan_ratings = True

        if 'playlist' in res:
            # Tell playlist view to update its status.
            redis_publisher = RedisPublisher(facility='piremote', broadcast=True)
            redis_publisher.publish_message(RedisMessage('playlist'))

        if 'player' not in res:
            return

        # Publish current player state via websocket via redis broadcast.
        state = self.client.status()
        cur = self.client.currentsong()
        state_data = self.generate_status_data(state, cur)
        state_data['event'] = res
        msg = json.dumps(state_data)
        redis_publisher = RedisPublisher(facility='piremote', broadcast=True)
        redis_publisher.publish_message(RedisMessage(msg))

        # Check if playing and file changed --> insert into history if so.
        if 'state' in state and state['state'] == 'play':
            file = cur['file']
            if file != self.last_file:
                self.last_file = file
                if 'artist' in cur and 'title' in cur:
                    title = '%s - %s' % (cur['artist'], cur['title'])
                elif 'title' in cur:
                    title = cur['title']
                else:
                    no_ext = os.path.splitext(file)[0]
                    title = os.path.basename(no_ext).replace('_', ' ')
                self.insert_into_history(file, title)

    def check_party_mode_init(self):
        """Check if seed playlist uppon start."""
        self.ensure_connected()
        if self.connected:
            self.check_party_mode(res=[], force=True)

    def insert_into_history(self, file, title):
        """Insert song into history for current time.

        :param file: file information from MPD
        :param title: artist - title or filename without extension
        """
        db = DATABASES['default']
        conn = sqlite3.connect(database=db['NAME'], timeout=15)
        cur = conn.cursor()
        # 1st read updated status from settings table.
        # Non-updated rows need to be fixed if clock is not set correctly.
        # Fixing is done via piremote/commands when time is set via client.
        cur.execute('''SELECT value FROM piremote_setting WHERE key=?''', ('time_updated', ))
        updated = False
        row = cur.fetchone()
        if row is not None:
            updated = row[0] == '1'
        now = datetime.datetime.now()
        cur.execute('''INSERT INTO piremote_history (title, path, time, updated) VALUES (?,?,?,?)''',
                    (title, file, now, updated,))
        conn.commit()
        cur.close()
        conn.close()


class MPDService(threading.Thread):
    """Threaded mpd communicator service.

    Idle until something happens and check if random add songs (party mode)
    """
    def __init__(self, parent):
        """Keep reference to PiBlasterWorker to know when to leave."""
        threading.Thread.__init__(self)
        self.parent = parent
        self.idler = MPC_Idler(parent)

    def run(self):
        """Daemon loop for MPD service.
        Idle until any MPD event occurs and check if to do anything.

        NOTE: You should be sure to catch all exceptions or the MPD service thread will be dead forever.
        """
        try:
            self.idler.check_party_mode_init()
        except (ConnectionError, CommandError) as e:
            print('MPD INIT ERROR')
            print(e)
        except sqlite3.OperationalError as e:
            print('SQLITE ERROR {0}'.format(e))

        while self.parent.keep_run:
            try:
                self.idler.mpc_idle()
            except (ConnectionError, CommandError) as e:
                print('MPD ERROR')
                print(e)
                sleep(1)
            except sqlite3.OperationalError as e:
                print('SQLITE ERROR {0}'.format(e))

    @staticmethod
    def stop_idler():
        """Connect to MPD and switch on/off repeat once to create an idler
        event to give the idler loop the opportunity to exit normally.
        """
        client = MPDClient()
        client.timeout = 10
        client.connect('localhost', 6600)
        rep = int(client.status()['repeat'])
        client.repeat(1 if rep == 0 else 0)
        sleep(0.1)
        client.repeat(0 if rep == 0 else 1)

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
        return data

