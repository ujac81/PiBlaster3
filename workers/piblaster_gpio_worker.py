#!/usr/bin/env python3
""" pyblaster2.py -- Worker daemon for piremote app.

Enable party mode for music player daemon, perform uploads, read/write GPIOs.

Communication to piremote app via SQL database

@Author Ulrich Jansen <ulrich.jansen@rwth-aachen.de>
"""

import os
import posix
import select
import signal
import time

from PiBlaster3.settings import *
if PB_USE_GPIO:
    from workers.gpio import LED, Buttons


class PiBlasterGpioWorker:
    """Worker daemon for piremote"""

    def __init__(self):
        """Create uploader and mpd service threads."""
        self.keep_run = True  # run daemon as long as True
        self.is_vassal = 'UWSGI_VASSAL' in os.environ
        self.led = None
        self.buttons = None
        self.pipe = None
        if PB_USE_GPIO:
            self.led = LED(self)
            self.buttons = Buttons(self)

    def run(self):
        """daemonize, start threads and enter daemon loop."""
        if not DEBUG and not self.is_vassal:
            # No fork in debug mode and not in uwsgi vassal mode.
            self.daemonize()
        else:
            print('PiBlasterWorker running in debug or as vassal')

        if PB_USE_GPIO:
            from workers.gpio import PB_GPIO
            PB_GPIO.init_gpio()
            self.led.init_leds()
            self.led.show_init_done()
            self.buttons.start()

        self.daemon_loop()

        if PB_USE_GPIO:
            self.buttons.join()
            self.led.join()
            PB_GPIO.cleanup(self)

    def make_pipe(self):
        """
        
        :return: 
        """
        if os.path.exists(PB_GPIO_PIPE):
            os.remove(PB_GPIO_PIPE)
        os.umask(0o000)
        os.mkfifo(PB_GPIO_PIPE, 0o666)
        self.pipe = posix.open(PB_GPIO_PIPE, posix.O_RDWR)

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

        self.print_message("Entering daemon loop...")

        poll_count = 0
        led_count = 1
        while self.keep_run:

            poll_count += 1

            time.sleep(50. / 1000.)  # 50ms default in config

            # Check if we can read from pipe
            r, w, x = select.select([self.pipe], [], [], 0)
            if self.pipe in r:
                line = os.read(self.pipe, 1024).decode('utf-8').split()
                print('PIPE READ %s' % line)

            if PB_USE_GPIO:
                self.buttons.read_buttons()
                if poll_count % 10 == 0:
                    self.led.play_leds(led_count)
                led_count += 1

        self.print_message('LEAVING')
        # Flash red and yellow led after exit (to indicate shutdown process)
        if PB_USE_GPIO:
            self.led.reset_leds()
            self.led.set_led_yellow()
            self.led.set_led_red()

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
    blaster_worker = PiBlasterGpioWorker()
    blaster_worker.run()
