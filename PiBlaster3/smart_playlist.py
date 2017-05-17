"""smart_playlist.py -- Apply smart filters to create playlist
"""

from piremote.models import Rating
from piremote.models import SmartPlaylist, SmartPlaylistItem, SmartPlaylistItemPayload

from django.core.exceptions import ObjectDoesNotExist


class ApplySmartPlaylist:
    """
    """

    def __init__(self, filter_id, amount):
        """
        
        :param filter_id: 
        :param amount: 
        """
        self.filter_id = filter_id
        self.amount = amount
        self.error = False
        self.result_string = 'No filter applied'

    def apply_filters(self, plname):
        """ 
        """
        try:
            s = SmartPlaylist.objects.get(id=self.filter_id)
        except ObjectDoesNotExist:
            self.error = True
            self.result_string = 'No such filter id {0}'.format(self.filter_id)
            return

        qfilters = SmartPlaylistItem.objects.filter(playlist=s).exclude(itemtype=SmartPlaylistItem.EMPTY).order_by('position')
        qrating = Rating.objects.all()

        # first apply all filters with weight 1
        for filt in qfilters.filter(weight=1):
            print('WEIGHT 1 FILTER {0}'.format(filt.itemtype))

        # Apply weighted filters on remaining items
        for filt in qfilters.exclude(weight=1).exclude(weight=0):
            print('WEIGHT <1 FILTER {0}'.format(filt.itemtype))

        self.result_string = '{} items added to playlist {}'.format(self.amount, plname)
