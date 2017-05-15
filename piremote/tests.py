# piremote/tests.py -- Unit tests for all views.

from django.test import TestCase
from django.test import Client

import time


class IndexTests(TestCase):
    """Unit tests for main view"""

    def test_can_load_index(self):
        client = Client()
        response = client.get('/piremote/')
        self.assertIs(response.status_code, 200)

    def test_cmd_settime(self):
        client = Client()
        local = time.mktime(time.localtime()) * 1000
        response = client.post('/piremote/ajax/command/', dict(cmd='settime', payload=[local]))
        self.assertIs(response.json()['ok'], 1)

    def test_status(self):
        client = Client()
        response = client.get('/piremote/ajax/status/').json()
        self.assertTrue('state' in response)

    def test_mixer(self):
        client = Client()
        response = client.get('/piremote/ajax/mixer/', {'class': 'volume'}).json()
        self.assertIs(response['ok'], 1)

    def test_equalizer(self):
        client = Client()
        response = client.get('/piremote/ajax/mixer/', {'class': 'equalizer'}).json()
        self.assertIs(response['ok'], 1)


class PlaylistTests(TestCase):
    """Unit tests for playlist view"""

    def test_plinfo(self):
        client = Client()
        response = client.get('/piremote/ajax/plinfo/').json()
        self.assertTrue('pl' in response)
        self.assertTrue('status' in response)
