"""mpc_thread.py -- threaded upload worker

"""

import psycopg2
import os
import shutil
from time import sleep
from mpd import MPDClient, ConnectionError, CommandError

from .settings import *


class UploadIdler:

    def __init__(self):
        self.upload_path = PB_UPLOAD_DIR
        self.upload_sources = PB_UPLOAD_SOURCES
        self.space_avail = None
        self.client = None
        self.connected = False

    def check_for_uploads(self):
        """

        :return:
        """
        db = DATABASES['default']
        conn = psycopg2.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'], host=db['HOST'])
        cur = conn.cursor()

        got_file = True
        did_upload = False
        while got_file:
            cur.execute('''SELECT * FROM piremote_upload ORDER_BY(path) LIMIT 1''')
            res = cur.fetchone()
            if res is None:
                got_file = False
            else:
                remove = res[1]
                if self.do_upload(remove):
                    did_upload = True
                cur.execute("DELETE FROM piremote_upload WHERE \"path\" = %s", (remove,))
                conn.commit()

            sleep(0.1)  # don't block CPU too much if this thread goes insane here.

        cur.close()
        conn.close()

        if did_upload:
            self.mpd_update()
        return

    def do_upload(self, filename):
        """

        :param filename:
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
            except OSError:
                print('MKDIR FAILED: '+dirname)
                return False

        # perform copy
        try:
            shutil.copy(filename, dest)
        except IOError:
            print('COPY FAILED: ' + dest)
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
        """

        :return:
        """
        self.client = MPDClient()
        if not self.mpd_connect():
            return
        self.client.update()


def upload_idler():
    ui = UploadIdler()
    ui.check_for_uploads()
