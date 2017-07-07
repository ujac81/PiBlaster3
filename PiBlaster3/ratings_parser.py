"""ratings_parser.py -- parse ratings received from XML file.
"""

import xml.etree.ElementTree as ET

from piremote.models import Rating
from django.core.exceptions import ObjectDoesNotExist

from .helpers import *


class RatingsParser:
    """Parse uploaded ratings from XML and apply to database.
    
    TODO: add other rating formats like banshee XML database or such.
    """

    def __init__(self, name, data):
        """Initialize XML parser from uploaded file content.

        :param name: name of the uploaded file
        :param data: file data
        """
        self.errors = []
        self.parsed_ratings = []
        self.not_parsed_ratings = []
        self.skipped_ratings = []
        self.filename = name
        self.tree = ET.ElementTree(ET.fromstring(data))
        self.root = self.tree.getroot()
        self.q_all = Rating.objects.all()

        raise_sql_led()
        if self.root.tag == 'django-objects' and 'version' in self.root.attrib and self.root.attrib['version'] == '1.0':
            self.parse_django()
        else:
            self.errors.append('UNKNOWN XML File Type: %s' % self.root.tag)

        clear_sql_led()

    def parse_django(self):
        """Parser for XML files exported by PiBlaster3"""

        for o in [x for x in self.root if x.tag == 'object']:
            path = o.find("field[@name='path']").text
            rating = int(o.find("field[@name='rating']").text) or 0
            artist = o.find("field[@name='artist']").text or ''
            album = o.find("field[@name='album']").text or ''
            title = o.find("field[@name='title']").text or ''
            self.apply_rating(path, artist, album, title, rating)

    def apply_rating(self, path, artist, album, title, rating):
        """Try to apply rating to SQL db.
        
        :param path: as found in db -- django db might start with local music path, others with absolute paths.
        :param artist: tag 
        :param album: tag
        :param title: tag 
        :param rating: [0-5]
        """
        try:
            q = Rating.objects.get(path=path)
            if q.rating != rating:
                q.rating = rating
                q.original = False
                q.save()
                self.parsed_ratings.append(['{} [{}]'.format(path, rating)])
            else:
                self.skipped_ratings.append(['{} [{}]'.format(path, rating)])
            return
        except ObjectDoesNotExist:
            pass

        # Check for last_dir/filename.mp3 match
        reminder = '/'.join(path.split('/')[-2:])
        q = self.q_all.filter(path__iendswith=reminder)
        if len(q) > 0:
            q2 = q.exclude(rating=rating)
            if len(q2) > 0:
                q2.update(rating=rating, original=False)
                self.parsed_ratings.append(['{} [{}]'.format(reminder, rating)])
            else:
                self.skipped_ratings.append(['{} [{}]'.format(reminder, rating)])
            return

        if title != '' and artist != '':
            # Check if album/artist/title matches
            q = self.q_all.filter(artist__iexact=artist).filter(title__icontains=title)
            if len(q) > 0:
                q2 = q.exclude(rating=rating)
                if len(q2) > 0:
                    q.update(rating=rating, original=False)
                    self.parsed_ratings.append(['{} - {} [{}]'.format(artist, title, rating)])
            else:
                self.skipped_ratings.append(['{} - {} [{}]'.format(artist, title, rating)])
            return

        # reached if rating cannot be applied
        self.not_parsed_ratings.append([path])
