"""commands.py -- perform commands like shutdown, check password, etc.

"""

from subprocess import Popen, PIPE, DEVNULL


class Commands:
    """Backend for AJAX POST /piremote/ajax/command """

    def __init__(self):
        """load password etc.
        """
        self.confirm_pass = 'ullipw'  # TODO: read from config

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
            return {'cmd': cmd, 'ok': 1, 'status': 'Powering off system.'}

        return {'cmd': cmd, 'error': 'Unknown command %s' % cmd}
