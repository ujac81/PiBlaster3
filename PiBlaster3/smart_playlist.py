"""smart_playlist.py -- Apply smart filters to create playlist
"""

from piremote.models import Rating
from piremote.models import SmartPlaylist, SmartPlaylistItem, SmartPlaylistItemPayload


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
        self.result_string = '{} items added to playlist {}'.format(self.amount, plname)
