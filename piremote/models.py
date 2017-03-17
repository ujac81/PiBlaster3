from django.db import models

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

        return {'status': 'Set %s to %s.' %(key, value)}


