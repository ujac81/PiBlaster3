"""alsa.py -- access to volume mixers and equalizer

Communicate with alsa audio mixer and equalizer via amixer command.
"""

import re
from subprocess import Popen, PIPE
from django.conf import settings

from .mpc import MPC
from .helpers import flash_command_led


class AlsaMixer:
    """Control alsa mixer master channel and equalizer plugin if found."""

    def __init__(self):
        """Get names of equalizer channels if such.
        """
        self.sudo_prefix = settings.PB_ALSA_SUDO_PREFIX
        self.volume_channels = settings.PB_ALSA_CHANNELS

    def get_amixer_volume(self, item):
        """Return volume retrieved from amixer -M get ITEM output.

        :param item: channel string like 'Master' or 'Channel'. See `alsamixer'
        :return: {name: item, value: Volume int in [0, 100]}
        """
        res = {'name': item}
        cmd = ['amixer', '-M', 'get', "\"%s\"" % item]
        if len(self.sudo_prefix):
            cmd = [self.sudo_prefix] + cmd
        channels = Popen(' '.join(cmd), shell=True, stdout=PIPE, stderr=PIPE). \
            communicate()[0].decode('utf-8').split('\n')
        for chan in channels:
            m = re.search(r"\[(\d+)%\]", chan)
            if m is not None:
                res['value'] = int(m.group(1))
        return res

    def get_volume_vals(self):
        """Return all volume values for all channels in PB_ALSA_CHANNELS list.

        :return: [{name: item1, value: volume1}, ....]
        """
        mpc = MPC()
        res = [{'name': 'Player', 'value': mpc.get_status_int('volume')}]
        for i, item in enumerate(self.volume_channels):
            res.append(self.get_amixer_volume(item))
        return res

    def set_volume_val(self, mixer_id, val):
        """Set mapped volume value for mixer item

        :param mixer_id: index in PB_ALSA_CHANNELS from settings (+1 for mpd client)
        :param val: integer value in [0, 100]
        :return: set volume value in [0, 100]
        """
        if mixer_id == 0:
            mpc = MPC()
            mpc.set_volume(val)
            return mpc.volume()
        else:
            cmd = ['amixer', '-M', 'set', "\"%s\"" % self.volume_channels[mixer_id-1], '%d%%' % val]
            if len(self.sudo_prefix):
                cmd = [self.sudo_prefix] + cmd
            flash_command_led()
            channels = Popen(' '.join(cmd), shell=True, stdout=PIPE, stderr=PIPE).communicate()[0].decode('utf-8').split('\n')
            for chan in channels:
                m = re.search(r"\[(\d+)%\]", chan)
                if m is not None:
                    return int(m.group(1))
        return 0

    def get_equal_vals(self):
        """Get list of int values for equalizer channels.
        :return: [{name: '3 kHz', value: 66}, ....]
        """
        cmd = ["amixer", "-D", "equal", "contents"]
        if len(self.sudo_prefix):
            cmd = [self.sudo_prefix] + cmd

        channels = Popen(cmd, stdout=PIPE, stderr=PIPE).\
            communicate()[0].decode('utf-8').split('\n')

        res = []
        cur_channel = None
        for chan in channels:
            name = [x for x in chan.split(',') if x.startswith('name=')]
            if len(name) == 1:
                cur_channel = ' '.join(name[0].split()[1:3])
            m = re.search('values=(\d+),(\d+)', chan)
            if m is not None:
                val = (int(m.group(1)) + int(m.group(2))) / 2
                res.append({'name': cur_channel, 'value': val})
        return res

    def set_equal_channel(self, chan, val):
        """Set equalizer channel by channel id.
        Invokes `amixer -D equal cset numid=(chan+1) (val)`.
        :param chan: channel as integer value [0..N_channels-1].
        :param val: value between 0 and 100
        """
        if val < 0:
            val = 0
        if val > 100:
            val = 100

        cmd = ["amixer", "-D", "equal", "cset", "numid=%d" % (chan+1), "%s" % val]
        if len(self.sudo_prefix):
            cmd = [self.sudo_prefix] + cmd
        flash_command_led()
        Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()

        cmd = ['amixer', '-D', 'equal', 'cget', "numid=%d" % (chan+1)]
        if len(self.sudo_prefix):
            cmd = [self.sudo_prefix] + cmd
        channels = Popen(' '.join(cmd), shell=True, stdout=PIPE, stderr=PIPE). \
            communicate()[0].decode('utf-8').split('\n')
        for chan in channels:
            m = re.search(r": values=(\d+)", chan)
            if m is not None:
                return int(m.group(1))

        return 0

    def get_channel_data(self, mixer_class):
        """Get full data for all volumes or all equalizer values.

        :param mixer_class: 'volume' or 'equalizer'
        :return: {data: [{name: mixer, value: 100}, ...]}
        """
        if mixer_class == 'volume':
            return {'ok': 1, 'data': self.get_volume_vals()}
        elif mixer_class == 'equalizer':
            return {'ok': 1, 'data': self.get_equal_vals()}

        return {'error_str': 'No such mixer class %s' % mixer_class}

    def set_channel_data(self, mixer_class, chan_id, value):
        """Set volume value for equalizer or mixer.

        :param mixer_class: 'equalizer' or 'volume'
        :param chan_id: index in channel name list.
        :param value: Integer value in [0, 100]
        :return: {status_str='some text', channel_index=N, value=M}
        """
        val = 0
        if mixer_class == 'equalizer':
            val = self.set_equal_channel(chan_id, value)
        elif mixer_class == 'volume':
            val = self.set_volume_val(chan_id, value)

        return {'status_str': 'Set %s channel %d to %d' % (mixer_class, chan_id, val), 'chan_id': chan_id, 'value': val}

