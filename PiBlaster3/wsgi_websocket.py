"""
WSGI config for PiBlaster3 project, redis websocket part.
"""

import os
import gevent.socket
import redis.connection
redis.connection.socket = gevent.socket
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PiBlaster3.settings")

from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

application = uWSGIWebsocketServer()
