"""mpc_thread.py -- threaded actions on playlist (like party mode).

"""

from mpd import MPDClient, ConnectionError, CommandError
import sqlite3
import random
from time import sleep


class MPC_Idler:
    """Keeps idle mode loop and party mode actions."""

    def __init__(self):
        self.client = MPDClient()
        self.client.timeout = 10
        self.connected = False
        random.seed()

    def connect(self):
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

    def idle(self):
        """Loop until mpd triggers an event (play, playlist, ...)"""
        res = self.client.idle()
        return res

    def check_party_mode(self, res):
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

        playlist_event = False
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

        db = sqlite3.connect('db.sqlite3', uri=True)
        cursor = db.cursor()
        cursor.execute('''SELECT key, value FROM piremote_setting''')
        for row in cursor:
            if row[0] == 'party_mode':
                party_mode = row[1] == '1'
            if row[0] == 'party_remain':
                party_remain = int(row[1])
            if row[0] == 'party_low_water':
                party_low_water = int(row[1])
            if row[0] == 'party_high_water':
                party_high_water = int(row[1])
        db.close()

        if not party_mode:
            return

        status = self.client.status()

        pos = int(status['song'])
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


def mpc_idler():
    mpc = MPC_Idler()
    if not mpc.connect():
        return
    mpc.check_party_mode(mpc.idle())


