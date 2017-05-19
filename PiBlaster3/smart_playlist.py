"""smart_playlist.py -- Apply smart filters to create playlist
"""

from piremote.models import Rating, History, SmartPlaylist, SmartPlaylistItem
from PiBlaster3.mpc import MPC

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from functools import reduce
import datetime
import operator


class ApplySmartPlaylist:
    """Selects items from rating table using filters from smart playlists.
    """

    def __init__(self, filter_id, amount):
        """Initialize the selector.
        
        :param filter_id: id of SmartPlaylist in database.
        :param amount: number of items the selector should add (max).
        """
        self.filter_id = filter_id
        self.amount = amount
        self.error = False
        self.result_string = 'No filter applied'

    def apply_filters(self, plname):
        """Iteratively select items from rating database using the given filters.
          
          After application of all filters add max self.amount items to playlist
          given by plname.
          
        :param plname: playlist to add to ('' for current).
        """
        try:
            s = SmartPlaylist.objects.get(id=self.filter_id)
        except ObjectDoesNotExist:
            self.error = True
            self.result_string = 'No such filter id {0}'.format(self.filter_id)
            return

        filters = SmartPlaylistItem.objects.filter(playlist=s).exclude(
            itemtype=SmartPlaylistItem.EMPTY).order_by('position')

        # first apply all filters with weight 1 directly
        q_list = []
        for filt in filters.filter(weight=1):
            q_item = self.get_q_item_from_filter(filt, plname)
            if q_item is not None:
                q_list.append(q_item)

        if len(q_list) == 0:
            qrating = Rating.objects.all().order_by('?')
        else:
            # apply all weight = 1 filters
            qrating = Rating.objects.filter(reduce(operator.and_, q_list)).order_by('?')

        if len(qrating) == 0:
            self.error = True
            self.result_string = 'Filter deselected all media items -- Nothing to add!'
            return

        # Apply weighted filters on remaining items:
        # Select items matching the filter (in) and items not matching the filter (out)
        # on remaining queryset. Randomly select that many items from both (in/out)
        # such that the weight ratio is reflected by the final selection.
        # Collect all ids and set current query to a randomized list of the
        # selected ids. Then apply next filter on remaining set and so on.
        for filt in filters.exclude(weight=1).exclude(weight=0):
            q_item = self.get_q_item_from_filter(filt, plname)
            if q_item is None:
                continue
            q_in = qrating.filter(q_item).order_by('?')
            q_out = qrating.exclude(q_item).order_by('?')
            len_in = len(q_in)
            len_out = int(len_in/filt.weight * (1-filt.weight))
            if len_out > len(q_out):
                # out data is too short, shorten in data
                len_out = len(q_out)
                len_in = int(len_out/(1-filt.weight)*filt.weight)

            ids1 = [x.id for x in q_in[:len_in]]
            ids2 = [x.id for x in q_out[:len_out]]
            # ids now holds a list of random ids in rating table with a mixture of the current filter.
            ids = ids1 + ids2

            if len(ids) == 0:
                self.error = True
                self.result_string = 'Filter deselected all media items -- Nothing to add!'
                return

            qrating = Rating.objects.filter(id__in=ids).order_by('?')

            # END for filt in filters with weight < 1 #

        mpc = MPC()

        # Filter intros from result
        files = []
        if len(filters.filter(itemtype=SmartPlaylistItem.PREVENT_INTROS)):
            mpc.ensure_connected()
            for item in qrating:
                info = mpc.client.find('file', item.path)
                if len(info) < 1:
                    continue
                time = int(info[0]['time']) if 'time' in info[0] else 1000
                title = info[0]['title'] if 'title' in info[0] else ''
                track = int(info[0]['track'].split('/')[0]) if 'track' in info[0] else 0
                if time < 60:
                    continue  # prevent too short songs
                if 'intro' in title.lower() and time < 120:
                    continue  # intro in song name and time less than 2 minutes
                if 'overture' in title.lower() and time < 120:
                    continue  # overture in song name and time less than 2 minutes
                if 'outro' in title.lower() and time < 180:
                    continue  # outros
                if 'intro' in title.lower() and track == 1 and time < 180:
                    continue  # intro in first song name and time less than 3 minutes

                files.append(item.path)
                if len(files) == self.amount:
                    break
        else:
            files = [x.path for x in qrating[:self.amount]]

        if len(files) == 0:
            self.error = True
            self.result_string = 'Filter deselected all media items -- Nothing to add!'
            return

        self.result_string = mpc.playlist_action('append', plname, files)

    @staticmethod
    def get_q_item_from_filter(filt, plname=''):
        """Translate filter item to django Q object for queries
        
        :param filt: SmartPlaylistItem item
        :return: Query item or None if filter broken
        """
        q_item = None

        # # # Filters without payload (prevent xxx) # # #

        if filt.itemtype == SmartPlaylistItem.PREVENT_LIVE:
            # Exclude '(live', '[live' and '....live' strings in album and title
            q_item = ~(reduce(operator.or_, (Q(album__iendswith='live'),
                                             Q(album__icontains='(live'), Q(album__icontains='[live'),
                                             Q(title__icontains='(live'), Q(title__icontains='[live'))))
        elif filt.itemtype == SmartPlaylistItem.PREVENT_DUPLICATES:
            # Get files in target playlist end exclude them
            mpc = MPC()
            if plname == '':  # current playlist
                pl_files = [x[6] for x in mpc.playlistinfo(0, -1)['data']]
            else:  # saved playlist
                pl_files = [x[0] for x in mpc.playlistinfo_by_name(plname)]
            if len(pl_files) > 0:
                q_item = ~Q(path__in=pl_files)
        elif filt.itemtype == SmartPlaylistItem.PREVENT_PLAYED_TODAY:
            # Drop items from recent history (last 24 hours)
            date_from = timezone.now() - datetime.timedelta(days=1)
            last_files = [x['path'] for x in History.objects.filter(time__gte=date_from).values('path')]
            if len(last_files) > 0:
                q_item = ~Q(path__in=last_files)

        if q_item is not None:
            if filt.negate:
                return ~q_item
            return q_item

        # # # Filters with simple payload (year, rating) # # #

        if filt.payload != '':
            int_payload = int(filt.payload)

            if filt.itemtype == SmartPlaylistItem.RATING_EQ:
                q_item = Q(rating=int_payload)
            elif filt.itemtype == SmartPlaylistItem.RATING_GTE:
                if not filt.negate:
                    return Q(rating__gte=int_payload)
                else:
                    # Negated rating GTE filter should not exclude 0 ratings
                    return ~Q(rating__in=list(range(1, int_payload+1)))
            elif filt.itemtype == SmartPlaylistItem.YEAR_LTE:
                q_item = Q(date__lte=int_payload)
            elif filt.itemtype == SmartPlaylistItem.YEAR_GTE:
                q_item = Q(date__gte=int_payload)

        if q_item is not None:
            if filt.negate:
                return ~q_item
            return q_item

        # # # Filters with payload list (genre, path, artist) # # #

        payloads = SmartPlaylistItem.get_payloads(filt.id)
        if len(payloads) == 0:
            return None

        if filt.itemtype == SmartPlaylistItem.IN_PATH:
            q_item = reduce(operator.or_, (Q(path__startswith=x) for x in payloads))
        elif filt.itemtype == SmartPlaylistItem.GENRE:
            q_item = Q(genre__in=payloads)
        elif filt.itemtype == SmartPlaylistItem.ARTIST:
            q_item = Q(artist__in=payloads)

        if q_item is not None:
            if filt.negate:
                return ~q_item
            return q_item
        return None
