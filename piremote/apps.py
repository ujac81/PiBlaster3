"""piremote/apps.py

ready function for application load.
"""

from django.apps import AppConfig

# from .models import Setting


class PiremoteConfig(AppConfig):
    name = 'piremote'

    def ready(self):
        print('SETTING')
        self.get_model('Setting').set_setting('time_updated', '0')
