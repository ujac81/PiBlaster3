"""ratings_scanner.py -- scan ratings from new files"""

from mpd import MPDClient, ConnectionError, CommandError
from mutagen.mp3 import HeaderNotFoundError
from PiBlaster3.settings import *
import mutagen
import os
import sqlite3


class RatingsScanner:
    """

    """

    def __init__(self, main):
        """

        """
        self.main = main

    def rescan(self):
        """

        :return:
        """
        if DEBUG:
            print("RESCANNING RATINGS")

        mpd_files = self.get_mpd_files()
        if len(mpd_files) == 0:
            self.main.rescan_ratings = False
            return

        db_files = self.get_db_files()
        if db_files is None:
            # there was an sqlite read error, retry next loop
            return

        music_path = self.get_music_path()
        if music_path is None:
            # there was an mpd error, retry next loop
            return

        to_add = []
        for item in mpd_files:
            if item not in db_files:
                rating = 0
                file = os.path.join(music_path, item)
                try:
                    m = mutagen.File(file)
                except HeaderNotFoundError as e:
                    print(file)
                    print('MUTAGEN ERROR {0}'.format(e))
                    to_add.append((item, 0, ))
                    continue

                try:
                    popm = m.tags.getall('POPM')
                except AttributeError:
                    # file type does not support tags
                    to_add.append((item, 0,))
                    continue

                if len(popm) > 0:
                    rat_count = 0
                    tot_rat = 0
                    for rat in popm:
                        if rat.email != 'Easy CD-DA Extractor':
                            tot_rat += rat.rating
                            if rat.rating > 0:
                                rat_count += 1
                    if rat_count > 0:
                        tot_rat /= rat_count
                        rating = tot_rat

                    if tot_rat > 0:
                        print(item)
                        print(popm)
                        print(rating)

                to_add.append((item, int(rating),))
            if not self.main.keep_run:
                # worker shut down in the meantime
                return

        to_remove = []
        for item in db_files:
            if item not in mpd_files:
                to_remove.append(item)

        if DEBUG:
            print('FOUND %d new files in mpd db' % len(to_add))
            print('FOUND %d files in db which are not in mpd db' % len(to_remove))

        self.alter_db('insert_many', to_add)
        self.alter_db('remove_many', to_remove)

        self.main.rescan_ratings = False

    @staticmethod
    def get_mpd_files():
        """

        :return:
        """
        client = MPDClient()
        client.timeout = 10
        try:
            client.connect('localhost', 6600)
            mpd_files = client.list('file')
        except ConnectionError:
            print("ERROR: CONNECT")
            return []
        except CommandError:
            print("ERROR: COMMAND")
            return []

        return mpd_files

    @staticmethod
    def get_db_files():
        """

        :return:
        """
        res = []
        try:
            db = DATABASES['default']
            conn = sqlite3.connect(database=db['NAME'], timeout=15)
            cur = conn.cursor()
            cur.execute('''SELECT path FROM piremote_rating''')
            for row in cur.fetchall():
                res.append(row[0])
            cur.close()
            conn.close()
        except sqlite3.OperationalError as e:
            print('SQLITE ERROR {0}'.format(e))
            return None

        return res

    @staticmethod
    def alter_db(what, payload):
        """

        :return:
        """
        res = []
        try:
            db = DATABASES['default']
            conn = sqlite3.connect(database=db['NAME'], timeout=15)
            cur = conn.cursor()

            if what == 'insert_many':
                cur.executemany('INSERT INTO piremote_rating (path, rating) VALUES (?, ?)', payload)
            elif what == 'remove_many':
                cur.executemany('DELETE FROM piremote_rating WHERE path=?', payload)
            else:
                print('ERROR: unknow alter db command: '+what)

            conn.commit()
            cur.close()
            conn.close()
        except sqlite3.OperationalError as e:
            print('SQLITE ERROR {0}'.format(e))
            return None

        return res

    @staticmethod
    def get_music_path():
        """

        :return:
        """
        client = MPDClient()
        client.timeout = 10
        try:
            client.connect(PB_MPD_SOCKET, 0)
            return client.config()
        except ConnectionError:
            print("ERROR: CONNECT SOCKET")
        except CommandError:
            print("ERROR: COMMAND SOCKET")

        return None
