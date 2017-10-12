"""ratings_scanner.py -- scan ratings from new files"""

from mpd import MPDClient, ConnectionError, CommandError, ProtocolError
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import HeaderNotFoundError
from mutagen.mp3 import MP3
from PiBlaster3.helpers import write_gpio_pipe
from PiBlaster3.settings import *
import mutagen
import os
import psycopg2
import time


class RatingsScanner:
    """Scan media items to SQL database, also tries to extract rating information (MPD doesn't)"""

    def __init__(self, main):
        """keep reference to main to know when to stop scanning loop.
        """
        self.main = main
        self.to_add = []  # store scanned result if insertion fails after scan
        self.to_remove = []  # store result if deletion fails after scan
        self.music_path = None  # store config query in get_music_path()
        self.conn = None
        self.cur = None
        self.client = MPDClient()
        self.client.timeout = 10
        self.mpd_reconnect()
        self.connected = False
        self.error = False

    def mpd_reconnect(self):
        """Try connect 5 times, if not successful self.connected will be False."""

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
                return True

        self.error = True
        return False

    def mpd_ensure_connected(self):
        """Make sure we are connected to mpd"""
        for i in range(5):
            try:
                self.client.status()
            except (ConnectionError, CommandError, ProtocolError, BrokenPipeError, ValueError):
                self.mpd_reconnect()

    def rescan(self):
        """Check if new items in MPD database which are not in SQL database.

        Read tags and append to database if so.
        Remove items from SQL database which are no longer in MPD database.

        Called via main daemon loop, triggered via MPD_Idler.
        Does not block too much, will leave scanning loop if keep_run is False in main.
        """
        self.main.print_message("RESCANNING RATINGS")

        if len(self.to_add) == 0 and len(self.to_remove) == 0:

            write_gpio_pipe("1 1\n3 1")  # raise yellow and blue led

            mpd_files = self.get_mpd_files()
            if mpd_files is None or len(mpd_files) == 0:
                # There was a mpd connect error, retry next loop.
                # Or: the music db was completely wiped out. Do nothing until there are files again.
                return

            # Get mpd files which are not in database
            not_in_db = self.get_db_files(not_in_database=mpd_files)
            if not_in_db is None:
                # there was an db read error, retry next loop
                return

            music_path = self.get_music_path()
            if music_path is None:
                # there was an mpd error, retry next loop
                return
            self.to_add = []
            for item in not_in_db:
                filename = os.path.join(music_path, item)
                self.to_add.append(self.scan_file(item, filename))
                if not self.main.keep_run:
                    # worker shut down in the meantime
                    return

            too_many = self.get_db_files(not_in_list=mpd_files)
            self.to_remove = []
            for item in too_many:
                self.to_remove.append((item,))

            if not self.main.keep_run:
                # worker shut down in the meantime
                return

            if DEBUG:
                self.main.print_message('FOUND %d new files in mpd db' % len(self.to_add))
                self.main.print_message('FOUND %d files in db which are not in mpd db' % len(self.to_remove))

            write_gpio_pipe("1 0\n3 0")  # clear yellow and blue led

            # Files to_add scanned and to_remove found #

        if len(self.to_add) > 0 and False:  # does not work for large DBs.
            # read times from MPD database for new items
            to_add_times = []
            write_gpio_pipe("1 1")  # raise yellow led
            client = MPDClient()
            client.timeout = 10
            try:
                client.connect('localhost', 6600)
            except ConnectionError:
                self.main.print_message("ERROR: CONNECT")
                return  # retry next loop
            for add_item in self.to_add:
                if not self.main.keep_run:
                    # worker shut down in the meantime
                    return
                add = list(add_item)
                try:
                    mpd_item = client.find('file', add_item[0])
                except (ConnectionError, CommandError):
                    self.main.print_message("ERROR: CONNECT")
                    return  # retry next loop
                if len(mpd_item) == 1 and 'time' in mpd_item[0]:
                    try:
                        length = int(mpd_item[0]['time'])
                    except ValueError:
                        length = 0
                    add[8] = length
                to_add_times.append(add)
            self.to_add = to_add_times
            write_gpio_pipe("1 0")  # clear yellow led

            # times scanned from MPD #

        if len(self.to_add) > 0 or len(self.to_remove) > 0:
            # apply to SQL
            write_gpio_pipe("3 1")  # raise blue led
            self.alter_db('insert_many', self.to_add)
            self.alter_db('remove_many', self.to_remove)
            write_gpio_pipe("3 0")  # clear blue led

        self.main.rescan_ratings = False  # do not rerun only on successful run
        self.to_add = []  # required to not block rating scanner for next run
        self.to_remove = []

    def get_mpd_files(self):
        """Fetch list of uri names from MPD databse.

        NOTE: mpd uris do not contain leading music path.

        :return: [local/uri1, local/uri2]
        """
        client = MPDClient()
        client.timeout = 10
        try:
            client.connect('localhost', 6600)
            mpd_files = client.list('file')
        except ConnectionError:
            self.main.print_message("ERROR: CONNECT")
            return None
        except CommandError:
            self.main.print_message("ERROR: COMMAND")
            return None

        return mpd_files

    def get_db_files(self, not_in_list=None, not_in_database=None):
        """Fetch list of uri names from SQL database.

        Uri names match MPD file names, so no leading music path.
        
        If both parameters are None, all db entries are returned.

        :param not_in_list: return those database items which are in list but in database (to_remove)
        :param not_in_database: return those list items which are not found in databse (to_add) 
        :return: [local/uri1, local/uri2]
        """
        res = []
        try:
            db = DATABASES['default']
            conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
            cur = conn.cursor()
            if not_in_database is not None:
                tuples = tuple([tuple([x]) for x in not_in_database])
                s_str = ', '.join(['%s'] * len(not_in_database))
                cur.execute('SELECT t.path FROM ( VALUES {} ) t(path) where not exists (SELECT path FROM piremote_rating r WHERE r.path = t.path)'.format(s_str), tuples)
            elif not_in_list is not None:
                cur.execute("SELECT path FROM piremote_rating WHERE path NOT IN %s", (tuple(not_in_list),))
            else:
                cur.execute('''SELECT path FROM piremote_rating''')
            for row in cur.fetchall():
                res.append(row[0])
            cur.close()
            conn.close()
        except psycopg2.OperationalError as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            return []

        return res

    def alter_db(self, what, payload):
        """Perform changes in database, (insert, delete, ....)"""
        try:
            db = DATABASES['default']
            conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
            cur = conn.cursor()

            if what == 'insert_many':
                try:
                    cur.executemany('INSERT INTO piremote_rating (path, title, artist, album, genre, date, rating, original, length) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', payload)
                except (psycopg2.DataError, psycopg2.InterfaceError):
                    for item in payload:
                        try:
                            cur.execute('INSERT INTO piremote_rating (path, title, artist, album, genre, date, rating, original, length) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', item)
                        except (psycopg2.DataError, psycopg2.InterfaceError, psycopg2.InternalError) as e:
                            self.main.print_message('INSERT ERROR: {0}'.format(e))
                            self.main.print_message(e.pgerror)
                            self.main.print_message(item)
                            return

            elif what == 'remove_many':
                cur.executemany('DELETE FROM piremote_rating WHERE path=(%s)', payload)
            elif what == 'deleteall':
                cur.execute('DELETE FROM piremote_rating')
            else:
                self.main.print_message('ERROR: unknow alter db command: '+what)

            conn.commit()
            cur.close()
            conn.close()
        except psycopg2.Error as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            self.main.print_message(e.pgcode)
            self.main.print_message(e.pgerror)
            return

    def get_next_zero_field_path(self):
        """Get next item's path from database where file size is zero.
        
        This is used in the worker loop of the rating scanner to slowly scan
        length and file sizes of files that are new in the database.
        
        :return: None if no such item, path otherwise.
        """
        if not self.reconnect_db():
            return None

        try:
            self.cur.execute('SELECT path FROM piremote_rating WHERE filesize=0')
            res = self.cur.fetchone()
            if res is None:
                return None
            if len(res) > 0:
                return res[0]
        except psycopg2.Error as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            self.main.print_message(e.pgcode)
            self.main.print_message(e.pgerror)
            return None

    def scan_length_and_size(self, scan_file):
        """Fetch time of file from MPD database and file size form OS and update Rating table.
         
        Invoked by PiBlasterWorker in daemon_loop if there are unscanned files.
        :param scan_file: MPD path via get_next_zero_field_path()
        """
        self.mpd_ensure_connected()
        try:
            res = self.client.find('file', scan_file)
        except (ConnectionError, CommandError, ProtocolError, BrokenPipeError, ValueError):
            # retry next loop
            return

        if len(res) < 1 or 'time' not in res[0]:
            return

        length = int(res[0]['time'])
        try:
            filesize = os.path.getsize(os.path.join(self.get_music_path(), scan_file))
        except FileNotFoundError:
            return

        if not self.reconnect_db():
            return

        try:
            self.cur.execute('UPDATE piremote_rating SET length=(%s), filesize=(%s) WHERE path=(%s)',
                             (length, filesize, scan_file))
            self.conn.commit()
            print("UPDATE {}: len={}, size={}".format(scan_file, length, filesize))
        except psycopg2.Error as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            self.main.print_message(e.pgcode)
            self.main.print_message(e.pgerror)
            return

    def reconnect_db(self):
        """Try to reconnect to database.
        Use this to reestablish connection to database if error occured.
        
        :return: True if connected without exception.
        """
        if self.cur is not None and self.cur.closed is False:
            # connection is established -- do nothing
            return True

        try:
            db = DATABASES['default']
            self.conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
            self.cur = self.conn.cursor()
            return True
        except psycopg2.Error as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            self.main.print_message(e.pgcode)
            self.main.print_message(e.pgerror)
            return False

    def get_music_path(self):
        """Try to connect to MPD via socket to receive music path.

        :return: '/local/music/path'
        """
        if self.music_path is not None:
            return self.music_path

        client = MPDClient()
        client.timeout = 10
        try:
            client.connect(PB_MPD_SOCKET, 0)
            self.music_path = client.config()
            return self.music_path
        except ConnectionError:
            self.main.print_message("ERROR: CONNECT SOCKET")
        except CommandError:
            self.main.print_message("ERROR: COMMAND SOCKET")

        return None

    @staticmethod
    def plain_filename(path):
        """Return filename without extension and replace _ by ' '"""
        no_ext = os.path.splitext(path)[0]
        return os.path.basename(no_ext).replace('_', ' ')

    def scan_file(self, item, file):
        """Try to open file with mutagen to extract information

        :param item: MPD uri descriptor (path without local music path)
        :param file: full file name
        :return: (uri, title, artist, album, genre, date, rating, original, time-dummy)
        """
        write_gpio_pipe('2 flash 0.2')

        try:
            m = mutagen.File(file)
        except HeaderNotFoundError as e:
            # (re)try to open by extension
            ext = os.path.splitext(file)[-1].lower()
            try:
                if ext == '.mp3':
                    m = mutagen.mp3.MP3(file)
                elif ext == '.ogg':
                    m = mutagen.oggvorbis.OggVorbis(file)
                elif ext == '.mpc':
                    m = mutagen.musepack.Musepack(file)
                elif ext == 'm4a':
                    m = mutagen.mp4.MP4(file)
                elif ext == 'flac':
                    m = mutagen.flac.FLAC(file)
                elif ext == 'wma':
                    m = mutagen.asf.ASF(file)
                else:
                    self.main.print_message(file)
                    self.main.print_message('MUTAGEN ERROR {0}'.format(e))
                    m = None
            except HeaderNotFoundError as e:
                self.main.print_message(file)
                self.main.print_message('MUTAGEN ERROR 2 {0}'.format(e))
                m = None

        if m is None:
            self.main.print_message('NO TAGS FOR ' + file)
            return item, self.plain_filename(file), '', '', '', 0, 0, True, 0,
        elif type(m) == mutagen.mp3.MP3:
            return self.parse_mp3(item, m, file)
        elif type(m) == mutagen.oggvorbis.OggVorbis:
            return self.parse_ogg(item, m, file)
        elif type(m) == mutagen.musepack.Musepack:
            return self.parse_mpc(item, m, file)
        elif type(m) == mutagen.flac.FLAC:
            return self.parse_ogg(item, m, file)
        elif type(m) == mutagen.mp4.MP4:
            return self.parse_m4a(item, m, file)
        elif type(m) == mutagen.asf.ASF:
            return self.parse_wma(item, m, file)

        self.main.print_message('UNKNOWN TYPE: ' + file)
        self.main.print_message(file)
        self.main.print_message(m)
        return item, self.plain_filename(file), '', '', '', 0, 0, True, 0,

    def parse_mp3(self, item, m, file):
        """Try to extract tags from MP3 file.

        Ratings are placed in POPM or TXXX:FMPS_Rating field and in range [0,255]

        :param item: MPD uri
        :param m: mutagen object
        :param file: full path
        :return: see scan_file()
        """
        try:
            audio = MP3(file, EasyID3)
        except HeaderNotFoundError as e:
            self.main.print_message(file)
            self.main.print_message('MUTAGEN ERROR {0}'.format(e))
            return item, self.plain_filename(file), '', '', '', 0, 0, True, 0,

        title, artist, album = ['']*3
        genre = 'unknown'
        date = 0
        rating = 0

        if 'title' in audio:
            title = audio['title'][0]
        if 'artist' in audio:
            artist = audio['artist'][0]
        if 'album' in audio:
            album = audio['album'][0]
        if 'date' in audio:
            date = self.conv_save_date(audio['date'][0], item)
        if 'genre' in audio:
            genre = audio['genre'][0]

        # Try to extract ratings from tags
        try:
            popm = m.tags.getall('POPM')
            fmps = m.tags.getall('TXXX:FMPS_Rating')
        except AttributeError:
            # file type does not support tags
            return item, self.plain_filename(file), '', '', '', 0, 0, True, 0,

        tot_rat = 0
        rat_count = 0

        if len(popm) > 0:
            for rat in popm:
                if rat.email != 'Easy CD-DA Extractor':
                    tot_rat += rat.rating
                    if rat.rating > 0:
                        rat_count += 1

        if len(fmps) > 0:
            for rat in fmps:
                rate = int(float(rat.text[0]) * 5 * 51)
                if rate > 0:
                    tot_rat += rate
                    rat_count += 1

        if rat_count > 0:
            tot_rat /= rat_count
            rating = tot_rat

        if title == '':
            title = self.plain_filename(file)

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51), True, 0,

    def parse_ogg(self, item, m, file):
        """Try to extract tags from ogg / flac file.

        Ratings are placed in fmps_rating field and in range [0.0, 1.0]

        :param item: MPD uri
        :param m: mutagen object
        :param file: full path
        :return: see scan_file()
        """
        title, artist, album = [''] * 3
        genre = 'unknown'
        date = 0
        rating = 0

        # OGG / FLAC / ... any vorbis style file
        if 'title' in m:
            title = m['title'][0]
        if 'artist' in m:
            artist = m['artist'][0]
        if 'album' in m:
            album = m['album'][0]
        if 'date' in m:
            date = m['date'][0]
        if 'genre' in m:
            genre = m['genre'][0]
        if 'fmps_rating' in m:
            rating = int(float(m['rating'][0]) * 5 * 51)

        if rating == 0:
            ratings = [float(x[1]) for x in m.tags if x[0].upper().startswith('RATING')]
            if len(ratings) > 0:
                rating = int(sum(ratings)*5.0/len(ratings)+0.5) * 51

        if title == '':
            title = self.plain_filename(file)

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51), True, 0,

    def parse_mpc(self, item, m, file):
        """Try to extract tags from MPC file.

        No rating information so far.

        :param item: MPD uri
        :param m: mutagen object
        :param file: full path
        :return: see scan_file()
        """
        title, artist, album = [''] * 3
        genre = 'unknown'
        date = 0
        rating = 0

        if 'Title' in m:
            title = m['Title'][0]
        if 'Artist' in m:
            artist = m['Artist'][0]
        if 'Album' in m:
            album = m['Album'][0]
        if 'Year' in m:
            date = m['Year'][0]
        if 'Genre' in m:
            genre = m['Genre'][0]

        if title == '':
            title = self.plain_filename(file)

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51), True, 0,

    def parse_m4a(self, item, m, file):
        """Try to extract tags from M4A file.

        No rating information so far.

        :param item: MPD uri
        :param m: mutagen object
        :param file: full path
        :return: see scan_file()
        """
        title, artist, album = [''] * 3
        genre = 'unknown'
        date = 0
        rating = 0

        if '\xa9nam' in m:
            title = m['\xa9nam'][0]
        if '\xa9ART' in m:
            artist = m['\xa9ART'][0]
        if '\xa9alb' in m:
            album = m['\xa9alb'][0]
        if '\xa9day' in m:
            date = m['\xa9day'][0]
        if '\xa9gen' in m:
            genre = m['\xa9gen'][0]

        if title == '':
            title = self.plain_filename(file)

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51), True, 0,

    def parse_wma(self, item, m, file):
        """Try to extract tags from WMA/ASF file.

        See http://help.mp3tag.de/main_tags.html

        :param item: MPD uri
        :param m: mutagen object
        :param file: full path
        :return: see scan_file()
        """
        title, artist, album = [''] * 3
        genre = 'unknown'
        date = 0
        rating = 0

        tags = m.tags
        get = tags.get('Title')
        if get is not None:
            title = str(get[0])
        get = tags.get('Author')
        if get is not None:
            artist = str(get[0])
        get = tags.get('WM/AlbumTitle')
        if get is not None:
            album = str(get[0])
        get = tags.get('WM/Genre')
        if get is not None:
            genre = str(get[0])
        get = tags.get('WM/Year')
        if get is not None:
            date = str(get[0])
        get = tags.get('WM/SharedUserRating')
        if get is not None:
            rating = int(round(int(str(get[0]))/99.0 * 5.0))

        if title == '':
            title = self.plain_filename(file)

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating / 51), True, 0,

    def conv_save_date(self, date, item):
        """Save conversion of date string (date could be like '2015-03-07T00:00:01')

        :return: integer (4 digit year)
        """
        try:
            return int(date)
        except ValueError:
            try:
                if len(date) < 4:
                    return 0
                return int(date[0:4])
            except ValueError:
                self.main.print_message(item)
                self.main.print_message("DATE CONVERSION FAILED: %s" % date)
                pass

        return 0
