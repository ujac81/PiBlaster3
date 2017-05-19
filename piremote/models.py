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
    time = models.DateTimeField(default=timezone.now)
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
            print('UPDATE')
            print(item)


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
            return dict(status_str='Unchanged rating for %s' % q.title)
        q.rating = rating
        q.original = False
        q.save()

        if rating == 0:
            return dict(status_str='Removed rating for %s' % q.title)
        return dict(status_str='Set rating for %s to %d' % (q.title, rating))

    @staticmethod
    def get_distinct(field):
        q = Rating.objects.values(field).distinct()
        return sorted([x[field] for x in q if x[field] != ''])


class SmartPlaylist(models.Model):
    """Smart playlist container for many smart playlist items.
    
    Used to seed current playlist or new playlist.    
    """
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=1024)
    time = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_json(idx):
        p = SmartPlaylist.objects.get(id=idx)
        return {
            'title': p.title,
            'description': p.description,
            'time': p.time.strftime("%Y-%m-%d %H:%M"),
            'items': SmartPlaylistItem.get_by_id(p.id)}

    @staticmethod
    def has_smart_playlist(title):
        return len(SmartPlaylist.objects.filter(title=title)) > 0

    @staticmethod
    def clone(idx):
        try:
            p = SmartPlaylist.objects.get(id=idx)
        except ObjectDoesNotExist:
            return 'No playlist to clone'

        new_pl = SmartPlaylist(title=p.title+' CLONE', description=p.description)
        new_pl.save()

        qitems = SmartPlaylistItem.objects.filter(playlist=p).order_by('id')
        for item in qitems:
            new_item = SmartPlaylistItem(playlist=new_pl,
                                         itemtype=item.itemtype,
                                         weight=item.weight,
                                         payload=item.payload,
                                         negate=item.negate,
                                         position=item.position)
            new_item.save()
            for payload in SmartPlaylistItem.get_payloads(item.id):
                pl = SmartPlaylistItemPayload(parent=new_item, item=payload)
                pl.save()
        return 'Smart playlist {0} cloned.'.format(p.title)


class SmartPlaylistItem(models.Model):
    """Selector item in smart playlist.
    
    Each selector carries a weight between [0..1] to adjust the strictness of the filter.
    Each selector carries a negate flag to invert the filter.
    
    """
    EMPTY = 0
    RATING_GTE = 1
    RATING_EQ = 2
    IN_PATH = 3
    IN_PLAYLIST = 12
    GENRE = 4
    ARTIST = 5
    YEAR_LTE = 6
    YEAR_GTE = 7
    PREVENT_INTROS = 8
    PREVENT_DUPLICATES = 9
    PREVENT_PLAYED_TODAY = 10
    PREVENT_LIVE = 11

    TYPE_CHOICES = (
        (EMPTY, 'empty'),
        (RATING_GTE, 'Rating greater or equal'),
        (RATING_EQ, 'Rating equal'),
        (IN_PATH, 'Path is one of'),
        (IN_PLAYLIST, 'Is in playlist'),
        (GENRE, 'Genre is one of'),
        (ARTIST, 'Artist is one of'),
        (YEAR_LTE, 'Year less or equal'),
        (YEAR_GTE, 'Year greater or equal'),
        (PREVENT_INTROS, 'Prevent intros'),
        (PREVENT_DUPLICATES, 'Prevent duplicates'),
        (PREVENT_PLAYED_TODAY, 'Not played last 24 hours'),
        (PREVENT_LIVE, 'Prevent live songs'),
    )
    playlist = models.ForeignKey('SmartPlaylist', on_delete=models.CASCADE)
    itemtype = models.PositiveSmallIntegerField(default=EMPTY, choices=TYPE_CHOICES)
    weight = models.FloatField(default=1.0)
    payload = models.CharField(max_length=256)
    negate = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField()

    @staticmethod
    def get_by_id(idx):
        q = SmartPlaylistItem.objects.filter(playlist=idx).order_by('position')
        return [[x.itemtype, x.weight, x.payload, x.negate, x.position, x.id,
                 SmartPlaylistItem.get_payloads(x.id)] for x in q]

    @staticmethod
    def get_payloads(idx):
        q = SmartPlaylistItemPayload.objects.filter(parent=idx).order_by('item')
        return [x.item for x in q]

    @staticmethod
    def add_new(idx):
        l = SmartPlaylist.objects.get(id=idx)
        q = SmartPlaylistItem.objects.filter(playlist=l).order_by('-position')
        if len(q) == 0:
            position = 0
        else:
            position = q[0].position + 1
        s = SmartPlaylistItem(playlist=l, position=position)
        s.save()

    @staticmethod
    def change_type(idx, new_type):
        s = SmartPlaylistItem.objects.get(id=idx)
        if s.itemtype == new_type:
            return
        s.itemtype = new_type
        s.payload = ''
        s.weight = 1
        s.negate = False
        s.save()
        SmartPlaylistItem.rm_payloads(idx)

    @staticmethod
    def move_item(idx, direction):
        s = SmartPlaylistItem.objects.get(id=idx)
        my_pos = s.position
        if direction == 'downitem':
            q = SmartPlaylistItem.objects.filter(playlist=s.playlist).filter(position__gte=my_pos + 1).order_by('position')
        else:
            q = SmartPlaylistItem.objects.filter(playlist=s.playlist).filter(position__lte=my_pos - 1).order_by('-position')

        if len(q) == 0:
            return
        exch_id = q[0].id
        s2 = SmartPlaylistItem.objects.get(id=exch_id)
        exch_pos = s2.position
        s.position = exch_pos
        s2.position = my_pos
        s.save()
        s2.save()

    @staticmethod
    def add_payload(idx, payload):
        s = SmartPlaylistItem.objects.get(id=idx)
        q = SmartPlaylistItemPayload.objects.filter(parent=s).filter(item=payload)
        if len(q) == 0:
            p = SmartPlaylistItemPayload(parent=s, item=payload)
            p.save()
            return True
        return False

    @staticmethod
    def rm_payload(idx, payload):
        s = SmartPlaylistItem.objects.get(id=idx)
        q = SmartPlaylistItemPayload.objects.filter(parent=s).filter(item=payload)
        if len(q) > 0:
            q.delete()
            return True
        return False

    @staticmethod
    def rm_payloads(idx):
        s = SmartPlaylistItem.objects.get(id=idx)
        SmartPlaylistItemPayload.objects.filter(parent=s).delete()

    @staticmethod
    def set_payloads(idx, payloads):
        s = SmartPlaylistItem.objects.get(id=idx)
        SmartPlaylistItemPayload.objects.filter(parent=s).delete()
        for item in payloads:
            p = SmartPlaylistItemPayload(parent=s, item=item)
            p.save()


class SmartPlaylistItemPayload(models.Model):
    """Payload row for SmartPlaylistItem
    
    E.g. on directory entry in IN_PATH filter
    """
    parent = models.ForeignKey('SmartPlaylistItem', on_delete=models.CASCADE)
    item = models.CharField(max_length=512)
