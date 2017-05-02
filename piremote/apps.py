"""piremote/apps.py

ready function for application load.
"""

from django.apps import AppConfig
from django.db.utils import ProgrammingError


class PiremoteConfig(AppConfig):
    name = 'piremote'

    def ready(self):
        try:
            self.get_model('Setting').set_setting('time_updated', '0')
        except LookupError:
            # database not migrated, skip setting of time_updated
            pass
        except ProgrammingError:
            # same
            pass
