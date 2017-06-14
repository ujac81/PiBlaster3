
from PiBlaster3.settings import *

import os


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

