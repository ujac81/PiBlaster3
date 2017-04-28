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
        for o in [x for x in self.root if x.tag == 'object']:
            path = o.find("field[@name='path']").text
            rating = int(o.find("field[@name='rating']").text)
            artist = o.find("field[@name='artist']").text
            album = o.find("field[@name='album']").text
            title = o.find("field[@name='title']").text
            parsed = False
            skipped = False
            try:
                q = Rating.objects.get(path=path)
                if q.rating != rating:
                    q.update(rating=rating)
                else:
                    skipped = True
                parsed = True
            except ObjectDoesNotExist:
                pass

            if not parsed:
                # Check for last_dir/filename.mp3 match
                reminder = '/'.join(path.split('/')[-2:])
                q = Rating.objects.filter(path__iendswith=reminder)
                if len(q) > 0:
                    q2 = q.exlude(rating=rating)
                    if len(q2) > 0:
                        q2.update(rating=rating)
                    else:
                        skipped = True
                    parsed = True

            if not parsed:
                # Check if album/artist/title matches
                q = Rating.objects.filter(title__icontains=title).\
                    filter(artist__icontains=artist).filter(album__icontains=album)
                if len(q) > 0:
                    q2 = q.exlude(rating=rating)
                    if len(q2) > 0:
                        q2.update(rating=rating)
                    else:
                        skipped = True
                    parsed = True

            app = [artist, album, title, path, rating]
            if parsed and not skipped:
                self.parsed_ratings.append(app)
            elif parsed and skipped:
                self.skipped_ratings.append(app)
            else:
                self.not_parsed_ratings.append(app)
