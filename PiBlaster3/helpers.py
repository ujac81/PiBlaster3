
from PiBlaster3.settings import *

import os
import time


def save_item(item, key):
    if key not in item:
        return ''
    res = item[key]
    if type(res) == str:
        return res
    if type(res) == list and len(res) > 0:
        return res[0]
    return ''


def save_artist_title(item):
    res = ''
    if 'artist' in item:
        res += save_item(item, 'artist') + ' - '
    if 'title' in item:
        res += save_item(item, 'title')
    else:
        no_ext = os.path.splitext(item['file'])[0]
        res = os.path.basename(no_ext).replace('_', ' ')
    return res


def save_title(item):
    if 'title' in item:
        res = save_item(item, 'title')
    else:
        no_ext = os.path.splitext(item['file'])[0]
        res = os.path.basename(no_ext).replace('_', ' ')
    return res


class PbLogger:
    """Logging object with integrated time duration measurement
    """

    def __init__(self, head='PROFILE'):
        """
        
        """
        self.head = head
        if PROFILE:
            self.start_time = time.time()
            self.start_interval = self.start_time

    def print_step(self, msg):
        """
        
        :param msg: 
        :return: 
        """
        if PROFILE:
            now = time.time()
            interval = int((now-self.start_interval)*1e3)
            total = int((now-self.start_time) * 1e3)
            self.start_interval = now
            print('[{}]: {} ({} ms step, {} ms total)'.format(self.head, msg, interval, total))

    def print(self, msg):
        """
        
        :param msg: 
        :return: 
        """
        if PROFILE:
            now = time.time()
            total = int((now-self.start_time) * 1e3)
            if total > 1000 and self.head == 'PROFILE VIEW':
                print('!!! Critical response time > 1s !!!')
            print('[{}]: {} ({} ms)'.format(self.head, msg, total))


def print_debug(msg):
    if DEBUG:
        print('[DEBUG] {}'.format(msg))


def write_gpio_pipe(msg):
    """Write message to GPIO pipe to raise/fall LEDs"""
    if PB_GPIO_PIPE is None or PB_USE_GPIO is False:
        # no command pipe or should not use GPIO
        return
    if not os.path.exists(PB_GPIO_PIPE):
        return
    try:
        w = open(PB_GPIO_PIPE, 'w')
        w.write(msg + '\n')
        w.flush()
    except OSError as e:
        print("PIPE WRITE ERROR: {}".format(e))


def flash_command_led(flash_time=0.333):
    """Flash white led for short period"""
    write_gpio_pipe('4 flash {}'.format(flash_time))


def raise_working_led():
    write_gpio_pipe('4 1')


def clear_working_led():
    write_gpio_pipe('4 0')


def raise_mpd_led():
    write_gpio_pipe('1 1')


def clear_mpd_led():
    write_gpio_pipe('1 0')


def flash_mpd_led(flash_time=0.333):
    write_gpio_pipe('1 flash {}'.format(flash_time))


def raise_sql_led():
    write_gpio_pipe('3 1')


def flash_sql_led(flash_time=0.333):
    write_gpio_pipe('3 flash {}'.format(flash_time))


def clear_sql_led():
    write_gpio_pipe('3 0')


def raise_upload_led():
    write_gpio_pipe('2 1')


def clear_upload_led():
    write_gpio_pipe('2 0')

