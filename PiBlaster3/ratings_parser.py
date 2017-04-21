"""ratings_parser.py -- parse ratings received from XML file.
"""

import xml.etree.ElementTree as ET


class RatingsParser:
    """

    """

    def __init__(self, name, data):
        """

        :param name:
        :param data:
        """
        self.errors = []
        self.filename = name
        self.tree = ET.ElementTree(ET.fromstring(data))
        self.root = self.tree.getroot()

        if self.root.tag == 'django-objects':
            self.parse_django()
        else:
            self.errors.append('UNKNOWN XML File Type: %s' % self.root.tag)

    def parse_django(self):
        """

        :return:
        """
        pass
