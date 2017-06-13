"""gpio.py -- Handle LEDs and buttons for PyBlaster.

@Author Ulrich Jansen <ulrich.jansen@rwth-aachen.de>
"""

import queue
import RPi.GPIO as GPIO
import sys
import threading
import time
from subprocess import Popen, PIPE, DEVNULL

from PiBlaster3.settings import *

GREEN = 0
YELLOW = 1
RED = 2
BLUE = 3
WHITE = 4


class PB_GPIO:
    """Prepare GPIOs for PyBlaster"""

    @staticmethod
    def init_gpio():
        if PIBLASTER_USE_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

    @staticmethod
    def cleanup():
        if PIBLASTER_USE_GPIO:
            GPIO.cleanup()


class LEDThread(threading.Thread):
    """Thread receiving commands to flash/unflash leds from LED via queue
    """

    def __init__(self, main, queue, queue_lock):
        threading.Thread.__init__(self)

        self.main = main
        self.queue = queue
        self.queue_lock = queue_lock
        self.init_done = False
        self.leds = []
        self.state = []

    def init_gpio(self):
        """Initialize GPIO ports and set init_done to true, so LEDs may be set.
        """

        self.leds = PIBLASTER_LEDS
        self.state = [0]*len(self.leds)

        for led in self.leds:
            GPIO.setup(led, GPIO.OUT)
        self.init_done = True

    def set_led_by_gpio(self, led, state):
        """Lower/Raise state indicator of LED.

        Each LED has a state counter which will flash the LED if > 0.
        Multiple actions may raise a LED and lower it, so state might be > 1,
        if two actions raised it. States below 0 are set to 0.
        Use -1 to force state to 0

        :param led: [0-4] led index (green, yel, red, blue, white)
        :param state: 1 = raise, 0 = lower, -1 = off
        """
        if not self.init_done:
            return

        if state == 1:
            self.state[led] += 1
        elif state == -1:
            self.state[led] = 0
        elif state == 0:
            self.state[led] -= 1

        if self.state[led] > 0:
            GPIO.output(self.leds[led], 1)

        if self.state[led] <= 0:
            self.state[led] = 0
            GPIO.output(self.leds[led], 0)

    def run(self):
        """Start LED commands queue reader loop.

        Wait until LED command pushed into queue and set LED state by queue
        command. Run until main wants to exit.
        """

        # try:
        self.init_gpio()
        while self.main.keep_run:
            try:
                led = self.queue.get(timeout=0.1)
                self.set_led_by_gpio(led[0], led[1])
            except queue.Empty:
                pass

        self.main.print_message("[THREAD] LED driver leaving...")
        for i in range(len(self.leds)):
            self.set_led_by_gpio(i, 0)
        self.set_led_by_gpio(PIBLASTER_LED_YELLOW, 1)


class LED:
    """LED GPIO handler for PyBlaster.

    Manage queue for LEDThread.
    """

    def __init__(self, main):
        """Initialize LEDThread and LED command queue"""

        self.main = main
        self.queue = queue.Queue()  # use one queue for all LEDS
        self.queue_lock = threading.Lock()
        self.led_thread = None
        if PIBLASTER_USE_GPIO:
            self.led_thread = LEDThread(self.main, self.queue, self.queue_lock)

    def init_leds(self):
        """Start LEDThread event loop.
        Do not call before LED ids are known via settings.
        """
        if self.led_thread is not None:
            self.led_thread.start()
            self.reset_leds()

    def show_init_done(self):
        """Let LEDs flash to indicate that PyBlaster initialization is done"""

        for i in range(1):
            for led in range(5):
                self.set_led(led, 1)
                time.sleep(0.1)
                self.set_led(led, 0)

    def reset_leds(self):
        """Force all LEDs to 0"""
        self.set_leds(-1)

    def set_led(self, num, state):
        """Set specific LED to state"""
        if self.led_thread is not None:
            self.queue.put([num, state])

    def set_leds(self, state=1):
        """Set all LEDs to state"""
        for led in range(5):
            self.set_led(led, state)

    def set_led_green(self, state=1):
        self.set_led(0, state)

    def set_led_yellow(self, state=1):
        self.set_led(1, state)

    def set_led_red(self, state=1):
        self.set_led(2, state)

    def set_led_blue(self, state=1):
        self.set_led(3, state)

    def set_led_white(self, state=1):
        self.set_led(4, state)

    def indicate_error(self):
        """Turn off all LEDs and raise red let"""
        self.set_leds(-1)
        self.set_led_red(1)

    def flash_led(self, led_code, flash_time):
        """Let a LED flash a certain amount of time and set LED port to LOW
        afterwards.

        Uses threading.Timer with flash_callback() as callback.
        """

        self.set_led(led_code, 1)
        timer = threading.Timer(flash_time, LED.flash_callback,
                                [self, led_code, 0])
        timer.start()

    @staticmethod
    def flash_callback(led, num, state):
        """Callback for timer routine.
        Let LED perform command after given time
        """
        led.set_led(num, state)

    def play_leds(self, count):
        """Lower current LED, raise next LED.
        """
        self.set_led((count-1) % 5, 0)
        self.set_led(count % 5, 1)

    def join(self):
        """Join LEDThread before exit."""
        if self.led_thread is not None:
            self.led_thread.join()


class ButtonThread(threading.Thread):
    """Check if button pressed and push press events into queue -- threaded

    Created by Buttons.
    """

    def __init__(self, main, pins, names, queue, queue_lock):
        """Init thread object

        Do not init GPIO pin here, might not be initialized.

        :param main: PyBlaster main object
        :param pins: GPIO port numbers in BCM mode
        :param names: Names of the button for queuing
        :param queue: queue object to push pressed events into
        :param queue_lock: lock queue while insertion
        """

        threading.Thread.__init__(self)
        self.main = main
        self.pins = pins
        self.names = names
        self.queue = queue
        self.queue_lock = queue_lock
        # Remember button state if button is pressed longer than one poll.

        # CAUTION: depending on your wiring and on some other unknown
        # circumstances, a released button might be in HIGH or LOW state.
        # For my wiring it's HIGH (1), so I need to invert all
        # "button pressed" logics. If your buttons are in LOW state, invert
        # all boolean conditions.
        self.prev_in = [1] * len(self.pins)  # init for released buttons

    def run(self):
        """Read button while keep_run in root object is true
        """

        # try:

        for i in range(len(self.pins)):
            GPIO.setup(self.pins[i], GPIO.IN)
            self.prev_in[i] = GPIO.input(self.pins[i])

        while self.main.keep_run:
            time.sleep(0.05)  # TODO: to config
            for i in range(len(self.pins)):
                inpt = GPIO.input(self.pins[i])
                if self.prev_in[i] != inpt:
                    # Note: depending on your wiring, the 'not' must be
                    # removed!
                    if inpt:
                        self.queue_lock.acquire()
                        self.queue.put([self.pins[i], self.names[i]])
                        self.queue_lock.release()
                self.prev_in[i] = inpt

        self.main.print_message("[THREAD] Button reader leaving...")


class Buttons:
    """Manage button thread and check if any button sent command to queue.

    Button thread will read button state every 0.0X seconds and queue
    changed state to this object's queue.
    Main loop will ask this object for button events and invoke read_buttons()
    if such.
    """

    def __init__(self, main):
        self.main = main
        self.queue = queue.Queue()  # use one queue for all buttons
        self.queue_lock = threading.Lock()
        self.btn_thread = None

    def start(self):
        """Let each button thread start.

        Not called in __init__() because of later GPIO init in LED class.
        """

        if PIBLASTER_USE_GPIO is False:
            return

        btns = PIBLASTER_BUTTONS
        
        self.btn_thread = \
            ButtonThread(self.main, btns,
                         ["green", "yellow", "red", "blue", "white"],
                         self.queue, self.queue_lock)

        self.btn_thread.start()

    def join(self):
        """Join all button threads after keep_run in root is False.
        """
        if self.btn_thread is not None:
            self.btn_thread.join()

    def has_button_events(self):
        """True if button events in queue
        """
        if not self.queue.empty():
            return True
        return False

    def read_last_button_event(self):
        """dry run queue and return last command if such -- None else

        :returns: None if no push event or [pin, button_name]
        """
        result = None

        while not self.queue.empty():
            self.queue_lock.acquire()
            try:
                result = self.queue.get_nowait()
            except queue.Empty:
                self.queue_lock.release()
                return None
            self.queue_lock.release()

        return result

    def read_buttons(self):
        """Execute command if button event found.

        Called by main loop if has_button_events() is true.
        """
        if not self.has_button_events():
            return

        event = self.read_last_button_event()
        if event is None:
            return

        button_color = event[1]
        self.main.print_message("--- Button \"%s\" pressed" % button_color)

        if button_color == "green":
            Popen('mpc toggle', shell=True, bufsize=1024,
                  stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True).wait()
        if button_color == "yellow":
            Popen('mpc next', shell=True, bufsize=1024,
                  stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True).wait()
        if button_color == "red":
            Popen('/sbin/poweroff', shell=True, bufsize=1024,
                  stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True).wait()
        if button_color == "blue":
            Popen('mpc volume -3', shell=True, bufsize=1024,
                  stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True).wait()
        if button_color == "white":
            Popen('mpc volume +3', shell=True, bufsize=1024,
                  stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True).wait()
