"""models.py -- models for piremote app.

If changes applied here, run
    ./manage.py makemigrations
    ./manage.py migrate
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

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
    title = models.CharField(max_length=256)
    path = models.FilePathField(max_length=500)
    time = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=False)

    @staticmethod
    def get_history(mode):
        """List of items in history

        :param mode: 'dates' for list of dates, 'YYYY-MM-DD' for specific date
        :return [[YYYY-MM-DD, Mon 1 Jan 2000] or [HH:MM, title, , , ,path]]
        """
        if mode == 'dates':
            dates = [timezone.localtime(i.time).date().isoformat() for i in History.objects.all().order_by('time')]
            return [[i, datetime.datetime.strptime(i, '%Y-%m-%d').strftime('%a %d %b %Y')]
                    for i in sorted(set(dates), reverse=True)]

        d1 = timezone.make_aware(datetime.datetime.strptime(mode, '%Y-%m-%d'))
        d2 = d1 + datetime.timedelta(days=1, seconds=-1)
        q = History.objects.filter(time__gte=timezone.localtime(d1)).filter(time__lte=timezone.localtime(d2)).order_by('-time')
        # put dummies on position 3 and 4 to have file item at position 5.
        return [[timezone.localtime(i.time).strftime('%H:%M'), i.title, None, None, None, i.path] for i in q]

    @staticmethod
    def search_history(pattern):
        """Search history titles for pattern
        
        :param pattern: search pattern to check for (case insensitive)
        :return: same as get_history
        """
        q = History.objects.filter(title__icontains=pattern).order_by('-time')
        return [[timezone.localtime(i.time).strftime('%d/%m/%Y %H:%M'), i.title, None, None, None, i.path] for i in q]

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


class Rating(models.Model):
    """MPD cannot store ratings for songs, so we copy the MPD database to SQL and enrich it by rating.

    Database is seeded by piblaster_worker process on any update of the MPD database.
    Ratings are read from file tags if such, ratings made by user here are stored in SQL database only.
    """
    path = models.FilePathField(max_length=500)
    title = models.CharField(max_length=256, default='')
    artist = models.CharField(max_length=256, default='')
    album = models.CharField(max_length=256, default='')
    genre = models.CharField(max_length=256, default='unknown')
    date = models.SmallIntegerField(default=0)
    rating = models.SmallIntegerField(default=0)  # [0..5]
    original = models.BooleanField(default=False)  # if rating came from file originally

    @staticmethod
    def get_rating(uri):
        """Get Rating for song from SQL

        :param uri: MPD uri
        :return: 0-5
        """
        try:
            return Rating.objects.values('rating').get(path=uri)['rating']
        except ObjectDoesNotExist:
            return 0

    @staticmethod
    def set_rating(uri, rating):
        """Rate song in database and return status or error string dict for JSON response.

        :param uri: MPD uri
        :param rating: 1-5 or 0 to remove
        :return: {error_str=''} or {status_str=''}
        """
        try:
            q = Rating.objects.get(path=uri)
        except ObjectDoesNotExist:
            return dict(error_str='Song to rate not found in database!')
        if rating == q.rating:
            return dict(status_str='Unchanged rating for %s' % q[0].title)
        q.rating = rating
        q.original = False
        q.save()

        if rating == 0:
            return dict(status_str='Removed rating for %s' % q[0].title)
        return dict(status_str='Set rating for %s to %d' % (q[0].title, rating))
