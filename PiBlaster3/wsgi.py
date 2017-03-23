"""
WSGI config for PiBlaster3 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
from threading import Thread

from django.core.wsgi import get_wsgi_application
from time import sleep

from PiBlaster3.mpc_thread import mpc_idler
from PiBlaster3.upload_thread import upload_idler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PiBlaster3.settings")

application = get_wsgi_application()


# Start a mpd client idler thread that checks for
# party mode and modifies playlist if necessary.
# Note I: This is a dirty thing to do so, we use uwsgi to spawn this thread.
# Note II: One can do that better (celery or else).
# Note III: Thread may die without affecting the web server, but will not be respawned.
def mpc_thread():
    # Note: do not call here -- uwsgi seems to freeze :/
    # mpc_check_party_mode_init()
    while True:
        sleep(0.01)
        try:
            mpc_idler()
        except:  # We know this is bad... Take care for sane behaviour of mpd_idler()
            pass


def upload_thread():
    # Note: do not call here -- uwsgi seems to freeze :/
    # mpc_check_party_mode_init()
    while True:
        sleep(1)
        upload_idler()



thread = Thread(target=mpc_thread)
thread.setDaemon(True)
thread.start()


thread2 = Thread(target=upload_thread)
thread2.setDaemon(True)
thread2.start()
