"""ratings_scanner.py -- scan ratings from new files"""

from mpd import MPDClient, ConnectionError, CommandError
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import HeaderNotFoundError
from mutagen.mp3 import MP3
from PiBlaster3.settings import *
import mutagen
import os
import psycopg2


class RatingsScanner:
    """Scan media items to SQL database, also tries to extract rating information (MPD doesn't)"""

    def __init__(self, main):
        """keep reference to main to know when to stop scanning loop.
        """
        self.main = main

    def rescan(self):
        """Check if new items in MPD database which are not in SQL database.

        Read tags and append to database if so.
        Remove items from SQL database which are no longer in MPD database.

        Called via main daemon loop, triggered via MPD_Idler.
        Does not block too much, will leave scanning loop if keep_run is False in main.
        """
        self.main.print_message("RESCANNING RATINGS")

        mpd_files = self.get_mpd_files()
        if mpd_files is None:
            # there was a mpd connect error, retry next loop
            return

        db_files = self.get_db_files()
        if db_files is None:
            # there was an db read error, retry next loop
            return

        music_path = self.get_music_path()
        if music_path is None:
            # there was an mpd error, retry next loop
            return

        to_add = []
        for item in mpd_files:
            if item not in db_files:
                filename = os.path.join(music_path, item)
                to_add.append(self.scan_file(item, filename))

            if not self.main.keep_run:
                # worker shut down in the meantime
                return

        to_remove = []
        for item in db_files:
            if item not in mpd_files:
                to_remove.append((item,))

        if not self.main.keep_run:
            # worker shut down in the meantime
            return

        if DEBUG:
            self.main.print_message('FOUND %d new files in mpd db' % len(to_add))
            self.main.print_message('FOUND %d files in db which are not in mpd db' % len(to_remove))

        self.alter_db('insert_many', to_add)
        self.alter_db('remove_many', to_remove)
        self.main.rescan_ratings = False

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

    def get_db_files(self):
        """Fetch list of uri names from SQL database.

        Uri names match MPD file names, so no leading music path.

        :return: [local/uri1, local/uri2]
        """
        res = []
        try:
            db = DATABASES['default']
            conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
            cur = conn.cursor()
            cur.execute('''SELECT path FROM piremote_rating''')
            for row in cur.fetchall():
                res.append(row[0])
            cur.close()
            conn.close()
        except psycopg2.OperationalError as e:
            self.main.print_message('PSQL ERROR {0}'.format(e))
            return None

        return res

    def alter_db(self, what, payload):
        """Perform changes in database, (insert, delete, ....)"""
        try:
            db = DATABASES['default']
            conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
            cur = conn.cursor()

            if what == 'insert_many':
                try:
                    cur.executemany('INSERT INTO piremote_rating (path, title, artist, album, genre, date, rating) VALUES (%s, %s, %s, %s, %s, %s, %s)', payload)
                except (psycopg2.DataError, psycopg2.InterfaceError):
                    for item in payload:
                        try:
                            cur.execute('INSERT INTO piremote_rating (path, title, artist, album, genre, date, rating) VALUES (%s, %s, %s, %s, %s, %s, %s)', item)
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

    def get_music_path(self):
        """Try to connect to MPD via socket to receive music path.

        :return: '/local/music/path'
        """
        client = MPDClient()
        client.timeout = 10
        try:
            client.connect(PB_MPD_SOCKET, 0)
            return client.config()
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
        :return: (uri, title, artist, album, genre, date, rating)
        """
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
            return item, self.plain_filename(file), '', '', '', 0, 0,
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
        return item, self.plain_filename(file), '', '', '', 0, 0,

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
            return item, self.plain_filename(file), '', '', '', 0, 0,

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
            return item, self.plain_filename(file), '', '', '', 0, 0,

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

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51),

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

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51),

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

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51),

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

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating/51),

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

        return item, title, artist, album, genre, self.conv_save_date(date, item), int(rating / 51),

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
