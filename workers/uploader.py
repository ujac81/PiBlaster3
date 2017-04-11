"""uploader.py -- threaded upload worker or piremote"""

import sqlite3
import os
import shutil
import threading
from time import sleep
from mpd import MPDClient, ConnectionError, CommandError

from PiBlaster3.settings import *


class UploadIdler:
    """Worker for Uploader thread.

     Includes check_for_uploads() routine which performs all the work if any uploads to be performed.
    """

    def __init__(self, main):
        """Keep reference to main object to leave uploader loop.

        :param main: PiBlasterWorker instance.
        """
        self.main = main
        self.upload_path = PB_UPLOAD_DIR
        self.upload_sources = PB_UPLOAD_SOURCES
        self.space_avail = None
        self.client = None
        self.connected = False

    def check_for_uploads(self):
        """Check if any uploadable files added to database.
        Upload them if such, return if not.
        Leave check loop if keep_run set to False in PiBlasterWorker.
        Remove uploaded files from database.
        Invoke MPD update if any uploads performed.

        Note: Concurrent access to sqlite3 database is safe if database is stored on local device.
        (file locks might fail on network file systems).
        """
        db = DATABASES['default']
        conn = sqlite3.connect(database=db['NAME'], timeout=15)
        cur = conn.cursor()

        got_file = True
        did_upload = False
        while got_file and self.main.keep_run:
            cur.execute('''SELECT * FROM piremote_upload ORDER BY path ASC LIMIT 1''')
            res = cur.fetchone()
            if res is None:
                got_file = False
            else:
                remove = res[1]
                if self.do_upload(remove):
                    did_upload = True
                cur.execute("DELETE FROM piremote_upload WHERE path=(?)", (remove,))
                conn.commit()

            sleep(0.1)  # don't block CPU too much if this thread goes insane here.

        cur.close()
        conn.close()

        if did_upload:
            self.mpd_update()
        return

    def do_upload(self, filename):
        """Check if file can be uploaded and perform upload.

        Remove leading entry from PB_UPLOAD_SOURCES settings from filename.
        Add PB_UPLOAD_DIR to destination file name.

        :param filename: full path of file to be uploaded.
        :return: True if file uploaded
        """

        # Check if
        src_size = os.path.getsize(filename)
        s = os.statvfs(self.upload_path)
        free = s.f_bavail * s.f_frsize
        # keep at least 200MB (logs, cache, whatever)
        if src_size > free - 1024 * 1024 * 200:
            print('DRIVE FULL, NOT UPLOADING')
            return False

        name = filename

        # get pure filename (without prefix)
        for src in self.upload_sources:
            if filename.startswith(src):
                name = filename.replace(src, '')

        if name.startswith('/'):
            name = name[1:]

        dest = os.path.join(self.upload_path, name)

        if os.path.isfile(dest):
            if os.path.getsize(dest) == src_size:
                # File exists - no upload
                return False

        # check dir exists
        dirname = os.path.dirname(dest)
        if not os.path.isdir(dirname):
            try:
                os.makedirs(dirname)
            except OSError as e:
                print('MKDIR FAILED: '+dirname)
                print("OSError: {0}".format(e))
                return False

        # perform copy
        try:
            shutil.copy(filename, dest)
        except IOError as e:
            print('COPY FAILED: ' + dest)
            print("IOError: {0}".format(e))
            return False

        return True

    def mpd_connect(self):
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

    def mpd_update(self):
        """Invoke mpd update if any file uploaded."""
        self.client = MPDClient()
        if not self.mpd_connect():
            return
        self.client.update()


class Uploader(threading.Thread):
    """Threaded worker for uploads.

    Performs file uploads if filenames added to upload table in database.
    """

    def __init__(self, parent):
        """Keep reference to PiBlasterWorker to know when to leave.
        :param parent: PiBlasterWorker
        """
        threading.Thread.__init__(self)
        self.parent = parent

    def run(self):
        """Endless thread loop until PiBlasterWorker leaves.

        Create UploadIdler() and check if it wants to upload anything.

        Note: make sure this thread does not throw uncaught exceptions, or upload thread will be dead.
        """
        while self.parent.keep_run:
            ui = UploadIdler(self.parent)
            try:
                ui.check_for_uploads()
            except sqlite3.OperationalError as e:
                print('SQLITE ERROR {0}'.format(e))
                pass
            sleep(1)
