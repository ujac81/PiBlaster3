"""
WSGI config for PiBlaster3 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PiBlaster3.settings")

application = get_wsgi_application()

try:
    import uwsgi
except ImportError:
    pass
#    print('WORKER: {}'.format(uwsgi.worker_id()))

