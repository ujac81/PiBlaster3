"""commands.py -- perform commands like shutdown, check password, etc.
"""

import time

from subprocess import Popen, PIPE, DEVNULL
from django.conf import settings

from piremote.models import History


class Commands:
    """Backend for AJAX POST /piremote/ajax/command """

    def __init__(self):
        """load password etc.
        """
        self.confirm_pass = settings.PB_CONFIRM_PASSWORD

    def perform_command(self, cmd, payload):
        """

        :return:
        """
        if cmd == 'checkpw':
            if payload[0] == self.confirm_pass:
                return {'cmd': cmd, 'ok': 1}
            return {'cmd': cmd, 'ok': 0}

        if cmd == 'poweroff':
            p = Popen('sudo /sbin/poweroff', shell=True, bufsize=1024,
                      stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
                      close_fds=True)
            p.wait()
            return {'cmd': cmd, 'ok': 1, 'status_str': 'Powering off system.'}

        if cmd == 'update':
            p = Popen('mpc update', shell=True, bufsize=1024,
                      stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
                      close_fds=True)
            p.wait()
            return {'cmd': cmd, 'ok': 1, 'status_str': 'Updating MPD database.'}

        if cmd == 'settime':
            if not settings.PB_SET_TIME:
                return {'cmd': cmd, 'ok': 1}
            t = int(int(payload[0])/1000)
            local = time.mktime(time.localtime())
            diff = t - local

            if abs(diff) > 60:
                # adjust clock time
                date = time.strftime('%d %b %Y %H:%M:%S', time.localtime(t))
                p = Popen('sudo /bin/date -s "%s"' % date, shell=True, bufsize=1024,
                          stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
                          close_fds=True)
                p.wait()
                History.update_history_times(diff)
                return {'cmd': cmd, 'ok': 1, 'status_str': 'Internal clock adjusted by %d seconds' % diff}

            return {'cmd': cmd, 'ok': 1}

        # Rescan no longer exists -- manually stop mpd, delete database and restart.
        #if cmd == 'rescan':
        #    p = Popen('mpc rescan', shell=True, bufsize=1024,
        #              stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL,
        #              close_fds=True)
        #   p.wait()
        #   return {'cmd': cmd, 'ok': 1, 'status_str': 'Rescanning MPD database.'}

        return {'cmd': cmd, 'error_str': 'Unknown command %s' % cmd}
