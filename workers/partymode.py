"""partymode.py -- threaded actions on playlist (like party mode)."""

from mpd import MPDClient, ConnectionError, CommandError
import sqlite3
import random
import threading
from time import sleep
from PiBlaster3.settings import *


class MPC_Idler:
    """Keeps idle mode loop and party mode actions."""

    def __init__(self):
        self.client = MPDClient()
        self.client.timeout = 10
        self.connected = False
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

    def idle(self):
        """Loop until mpd triggers an event (play, playlist, ...)"""
        res = self.client.idle()
        return res

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
        self.ensure_connected()
        if self.connected:
            res = self.client.idle()
            self.check_party_mode(res)

    def check_party_mode_init(self):
        """

        :return:
        """
        self.ensure_connected()
        if self.connected:
            self.check_party_mode(res=[], force=True)


class MPDService(threading.Thread):
    """

    """
    def __init__(self, parent):
        """

        :param parent:
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.idler = MPC_Idler()

    def run(self):
        """

        :return:
        """
        self.idler.check_party_mode_init()
        while self.parent.keep_run:
            self.idler.mpc_idle()

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

