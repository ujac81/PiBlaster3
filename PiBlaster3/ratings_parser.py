"""ratings_parser.py -- parse ratings received from XML file.
"""

import xml.etree.ElementTree as ET

from piremote.models import Rating


class RatingsParser:
    """

    """

    def __init__(self, name, data):
        """

        :param name:
        :param data:
        """
        self.errors = []
        self.parsed_ratings = []
        self.not_parsed_ratings = []
        self.filename = name
        self.tree = ET.ElementTree(ET.fromstring(data))
        self.root = self.tree.getroot()

        if self.root.tag == 'django-objects' and 'version' in self.root.attrib and self.root.attrib['version'] == '1.0':
            self.parse_django()
        else:
            self.errors.append('UNKNOWN XML File Type: %s' % self.root.tag)

    def parse_django(self):
        """

        :return:
        """
        for o in [x for x in self.root if x.tag == 'object']:
            path = o.find("field[@name='path']").text
            rating = int(o.find("field[@name='rating']").text)
            artist = o.find("field[@name='artist']").text
            album = o.find("field[@name='album']").text
            title = o.find("field[@name='title']").text
            q = Rating.objects.filter(path=path)
            parsed = False
            if len(q) > 0:
                q.update(rating=rating)
                parsed = True

            if not parsed:
                # Check for last_dir/filename.mp3 match
                reminder = '/'.join(path.split('/')[-2:])
                q = Rating.objects.filter(path__iendswith=reminder)
                if len(q) > 0:
                    q.update(rating=rating)
                    parsed = True

            if not parsed:
                # Check if album/artist/title matches
                q = Rating.objects.filter(title__icontains=title).\
                    filter(artist__icontains=artist).filter(album__icontains=album)
                if len(q) > 0:
                    q.update(rating=rating)
                    parsed = True

            app = [artist, album, title, path, rating]
            print(app)
            if parsed:
                self.parsed_ratings.append(app)
            else:
                self.not_parsed_ratings.append(app)
