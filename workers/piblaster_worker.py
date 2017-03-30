#!/usr/bin/env python3
""" pyblaster2.py -- Worker daemon for piremote app.

Enable party mode for music player daemon, perform uploads, read/write GPIOs.

Communication to piremote app via PostgreSQL database

@Author Ulrich Jansen <ulrich.jansen@rwth-aachen.de>
"""

import os
import signal
import time

from PiBlaster3.settings import *
from workers.uploader import Uploader
from workers.partymode import MPDService


class PiBlasterWorker:
    """Worker daemon for piremote"""

    def __init__(self):
        """

        :return:
        """
        self.keep_run = True  # run daemon as long as True
        self.uploader = Uploader(self)
        self.idler = MPDService(self)

    def run(self):
        """

        :return:
        """
        self.daemonize()
        self.uploader.start()
        self.idler.start()
        self.daemon_loop()
        MPDService.stop_idler()

    def daemon_loop(self):
        """

        :return:
        """
        while self.keep_run:

            time.sleep(50. / 1000.)  # 50ms

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
