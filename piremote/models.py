"""models.py -- models for piremote app.

If changes applied here, run
    ./manage.py makemigrations
    ./manage.py migrate
"""

from django.db import models
from django.conf import settings

import datetime
import os


class Setting(models.Model):
    """Key/value pairs for PiBlaster 3 settings.

    E.g.: party_moode, party_remain, ....
    """
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)

    @staticmethod
    def get_settings(payload):
        """Get settings for keys in payload.

        :param payload: array of setting keys to retrieve.
        :return: {key: value, ....}
        """
        res = {}
        for key in payload:
            value = ''
            q = Setting.objects.filter(key__exact=key)
            if q.count() == 0:
                # Create settings if not set so far.
                if key == 'party_mode':
                    value = '0'
                if key == 'party_remain':
                    value = '10'
                if key == 'party_low_water':
                    value = '5'
                if key == 'party_high_water':
                    value = '20'
                s = Setting(key=key, value=value)
                s.save()
            else:
                value = q[0].value
            res[key] = value

        return res

    @staticmethod
    def set_setting(key, value):
        """Setter for piremote app settings.

        :param key: key string
        :param value: value string
        :return: status message for status bar
        """
        q = Setting.objects.filter(key__exact=key)
        if q.count() == 0:
            s = Setting(key=key, value=value)
            s.save()
        else:
            q.update(value=value)

        return {'status_str': 'Set %s to %s.' % (key, value)}


class Upload(models.Model):
    """Upload queue table.

    Upload worker will drain this queue while uploading files.
    """
    path = models.CharField(max_length=500)

    @staticmethod
    def has_item(path):
        """"True if path exists in upload queue."""
        return Upload.objects.filter(path__exact=path).count() != 0

    @staticmethod
    def has_uploads():
        """True if any items in upload queue"""
        return Upload.objects.all().count() != 0

    @staticmethod
    def get_uploads():
        """List of items in upload queue"""
        return [i.path for i in Upload.objects.all().order_by('path')]

    @staticmethod
    def add_item(path):
        """Add item to queue.
        If item is directory, recursive add media files inside.
        """
        if Upload.has_item(path):
            return 0

        if os.path.isfile(path):
            if path.lower().endswith(settings.PB_MEDIA_EXT):
                u = Upload(path=path)
                u.save()
                return 1
            return 0

        all_files = [os.path.join(d, f)
                     for d, subd, files in os.walk(path)
                     for f in files if f.lower().endswith(settings.PB_MEDIA_EXT)]

        added = 0
        for f in all_files:
            if not Upload.has_item(f):
                u = Upload(path=f)
                u.save()
                added += 1

        return added


class History(models.Model):
    """History of songs played.

    history recorded to database by MPC_Idler via worker daemon.
    """
    title = models.CharField(max_length=100)
    path = models.FilePathField(max_length=500)
    time = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=False)

    @staticmethod
    def get_history(mode):
        """List of items in history

        :param mode: 'dates' for list of dates, 'YYYY-MM-DD' for specific date
        :return [[YYYY-MM-DD, Mon 1 Jan 2000] or [HH:MM, title, path]]
        """
        if mode == 'dates':
            dates = [i.time.date().isoformat() for i in History.objects.all().order_by('time')]
            return [[i, datetime.datetime.strptime(i, '%Y-%m-%d').strftime('%a %d %b %Y')]
                    for i in sorted(set(dates))]

        date = datetime.datetime.strptime(mode, '%Y-%m-%d').date()
        q = History.objects.filter(time__year=date.year).filter(time__month=date.month).filter(time__day=date.day).order_by('time')
        # put dummies on position 3 and 4 to have file item at position 5.
        return [[i.time.strftime('%H:%M'), i.title, None, None, None, i.path] for i in q]

    @staticmethod
    def update_history_times(diff):
        """Apply time diff to history item and flag as updated.

        This is necessary if the player device is started with an unknown clock state.
        The history will start recording with unset local hardware clock and updated=False flag.
        Upon first load of the main page the system time will be set to the time transmitted by the client.

        :param diff: client time - localtime
        """
        q = History.objects.filter(updated=False)
        for item in q:
            delta = datetime.timedelta(seconds=diff)
            item.time += delta
            item.updated = True
            item.save()
