#!/usr/bin/env python3
""" pyblaster2.py -- Worker daemon for piremote app.

Enable party mode for music player daemon, perform uploads, read/write GPIOs.

Communication to piremote app via SQL database

@Author Ulrich Jansen <ulrich.jansen@rwth-aachen.de>
"""

import os
import signal
import time

from PiBlaster3.settings import *
from workers.uploader import Uploader
from workers.partymode import MPDService
from workers.ratings_scanner import RatingsScanner


class PiBlasterWorker:
    """Worker daemon for piremote"""

    def __init__(self):
        """Create uploader and mpd service threads."""
        self.keep_run = True  # run daemon as long as True
        self.uploader = Uploader(self)
        self.idler = MPDService(self)
        self.scanner = RatingsScanner(self)
        self.rescan_ratings = True  # rescan ratings on boot
        self.is_vassal = 'UWSGI_VASSAL' in os.environ

    def run(self):
        """daemonize, start threads and enter daemon loop."""
        if not DEBUG and not self.is_vassal:
            # No fork in debug mode and not in uwsgi vassal mode.
            self.daemonize()
        else:
            print('PiBlasterWorker running in debug or as vassal')
        self.uploader.start()
        self.idler.start()
        self.daemon_loop()
        MPDService.stop_idler()

    def print_message(self, msg):
        """

        :param msg:
        :return:
        """
        if DEBUG or self.is_vassal:
            print('[WORKER] {0}'.format(msg))

    def daemon_loop(self):
        """Main daemon loop.

        uploader and party mode threaded,
        ratings scanner activated if idler found database update.

        :return:
        """

        while self.keep_run:

            time.sleep(100. / 1000.)  # 100ms
            if self.rescan_ratings:
                self.scanner.rescan()  # won't block too long

        self.print_message('LEAVING')

    def term_handler(self, *args):
        """ Signal handler to stop daemon loop"""
        self.keep_run = False

    def daemonize(self):
        """Fork process and install signal handler"""

        signal.signal(signal.SIGTERM, self.term_handler)
        signal.signal(signal.SIGINT, self.term_handler)
        try:
            pid = os.fork()
        except OSError:
            print("Failed to fork daemon")
            raise

        if pid == 0:
            os.setsid()
            try:
                pid = os.fork()
            except OSError:
                print("Failed to fork daemon")
                raise

            if pid == 0:
                os.chdir("/tmp")
                os.umask(0)
            else:
                exit(0)
        else:
            exit(0)


if __name__ == '__main__':
    blaster_worker = PiBlasterWorker()
    blaster_worker.run()
