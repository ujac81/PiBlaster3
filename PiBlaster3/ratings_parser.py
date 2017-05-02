"""ratings_parser.py -- parse ratings received from XML file.
"""

import xml.etree.ElementTree as ET

from piremote.models import Rating
from django.core.exceptions import ObjectDoesNotExist


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

        if self.root.tag == 'django-objects' and 'version' in self.root.attrib and self.root.attrib['version'] == '1.0':
            self.parse_django()
        else:
            self.errors.append('UNKNOWN XML File Type: %s' % self.root.tag)

    def parse_django(self):
        """Parser for XML files exported by PiBlaster3"""
        q_all = Rating.objects.all()
        for o in [x for x in self.root if x.tag == 'object']:
            path = o.find("field[@name='path']").text
            rating = int(o.find("field[@name='rating']").text) or 0
            artist = o.find("field[@name='artist']").text or ''
            album = o.find("field[@name='album']").text or ''
            title = o.find("field[@name='title']").text or ''
            parsed = False
            skipped = False
            try:
                q = Rating.objects.get(path=path)
                if q.rating != rating:
                    q.rating = rating
                    q.save()
                else:
                    skipped = True
                parsed = True
            except ObjectDoesNotExist:
                pass

            if not parsed:
                # Check for last_dir/filename.mp3 match
                reminder = '/'.join(path.split('/')[-2:])
                q = q_all.filter(path__iendswith=reminder)
                if len(q) > 0:
                    q2 = q.exclude(rating=rating)
                    if len(q2) > 0:
                        q2.update(rating=rating)
                    else:
                        skipped = True
                    parsed = True

            if not parsed and title + artist + album != '':
                # Check if album/artist/title matches
                q = q_all
                if title != '':
                    q = q.filter(title__icontains=title)
                if artist != '':
                    q = q.filter(artist__icontains=artist)
                if album != '':
                    q = q.filter(album__icontains=album)
                if len(q) > 0:
                    q2 = q.exclude(rating=rating)
                    if len(q2) > 0:
                        q2.update(rating=rating)
                    else:
                        skipped = True
                    parsed = True

            add = [artist, album, title, path, rating]
            if parsed and not skipped:
                self.parsed_ratings.append(add)
            elif parsed and skipped:
                self.skipped_ratings.append(add)
            else:
                self.not_parsed_ratings.append(add)
