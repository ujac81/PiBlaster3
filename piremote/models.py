from django.db import models

import os

# Create your models here.


class Setting(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)

    @staticmethod
    def get_settings(payload):
        """

        :param list:
        :return:
        """
        res = {}
        for key in payload:
            value = ''
            q = Setting.objects.filter(key__exact=key)
            if q.count() == 0:
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
        q = Setting.objects.filter(key__exact=key)
        if q.count() == 0:
            s = Setting(key=key, value=value)
            s.save()
        else:
            q.update(value=value)

        return {'status_str': 'Set %s to %s.' % (key, value)}


class Upload(models.Model):
    path = models.CharField(max_length=500)

    @staticmethod
    def has_item(path):
        return Upload.objects.filter(path__exact=path).count() != 0

    @staticmethod
    def has_uploads():
        return Upload.objects.all().count() != 0

    @staticmethod
    def get_uploads():
        return [i.path for i in Upload.objects.all().order_by('path')]

    @staticmethod
    def add_item(path):
        if Upload.has_item(path):
            return 0

        if os.path.isfile(path):
            if path.lower().endswith(('.mp3', '.ogg', '.flac', '.wma', '.wav')):
                u = Upload(path=path)
                u.save()
                return 1
            return 0

        all_files = [os.path.join(d, f)
                     for d, subd, files in os.walk(path)
                     for f in files if f.endswith(('.mp3', '.ogg', '.flac', '.wma', '.wav'))]

        added = 0
        for f in all_files:
            if not Upload.has_item(f):
                u = Upload(path=f)
                u.save()
                added += 1

        return added
