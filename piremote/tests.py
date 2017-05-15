from django.test import TestCase
from django.test import Client

# Create your tests here.


class IndexTests(TestCase):

    def test_can_load_index(self):
        client = Client()
        response = client.get('/piremote/')
        self.assertIs(response.status_code, 200)

    def test_can_load_upload_history(self):
        client = Client()
        response = client.get('/piremote/upload/history')
        self.assertIs(response.status_code, 200)
