"""commands.py -- perform commands like shutdown, check password, etc.

"""


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
            # TODO sudo /sbin/poweroff
            return {'cmd': cmd, 'ok': 1, 'status': 'Powering off system.'}

        return {'cmd': cmd, 'error': 'Unknown command %s' % cmd}
