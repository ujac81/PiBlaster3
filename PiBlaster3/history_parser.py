"""history_parser.py -- parse history received from XML file.
"""

import xml.etree.ElementTree as ET

from piremote.models import History, Rating
from django.core.exceptions import ObjectDoesNotExist
from .helpers import *

class HistoryParser:
    """Parse uploaded history from XML and apply to database.
    
    TODO: add other rating formats like banshee XML database or such.
    """

    def __init__(self, name, data):
        """Initialize XML parser from uploaded file content.

        :param name: name of the uploaded file
        :param data: file data
        """
        self.errors = []
        self.parsed_items = []
        self.not_parsed_items = []
        self.skipped_items = []
        self.filename = name
        self.tree = ET.ElementTree(ET.fromstring(data))
        self.root = self.tree.getroot()

        if self.root.tag == 'django-objects' and 'version' in self.root.attrib and self.root.attrib['version'] == '1.0':
            self.parse_django()
        else:
            self.errors.append('UNKNOWN XML File Type: %s' % self.root.tag)

    def parse_django(self):
        """Parser for XML files exported by PiBlaster3"""
        raise_sql_led()
        q_all = History.objects.all()
        insert = []  # for later insert into history
        for o in [x for x in self.root if x.tag == 'object']:
            path = o.find("field[@name='path']").text or None
            title = o.find("field[@name='title']").text or None
            time = o.find("field[@name='time']").text or None

            parsed = False
            skipped = False
            broken = False

            if path is None or title is None or time is None:
                broken = True
                parsed = True

            try:
                # time exists in history -> skip no matter which path we had
                History.objects.get(time=time)
                skipped = True
                parsed = True
            except ObjectDoesNotExist:
                pass

            if not parsed:
                # Check if we can find path in database -> merge
                q = q_all.filter(path=path)
                if len(q) > 0:
                    # We got a match -> direct insert
                    insert.append([title, path, time, True])
                    parsed = True
                else:
                    # Check if we find similar path in database -> merge
                    reminder = '/'.join(path.split('/')[-2:])
                    q = q_all.filter(path__iendswith=reminder)
                    if len(q) > 0:
                        # We found a file with same file name and dirname -> merge
                        insert.append([title, q[0].path, time, True])
                        parsed = True
                    else:
                        # No direct match in database -> insert as is
                        insert.append([title, path, time, True])
                        parsed = True

            add = [title, path, time, True]
            if broken:
                self.not_parsed_items.append(add)
            elif parsed and not skipped:
                self.parsed_items.append(add)
            elif parsed and skipped:
                self.skipped_items.append(add)
            else:
                self.not_parsed_items.append(add)

            # end for object in XML

        for item in insert:
            # We could do this faster, but should work.
            h = History(title=item[0], path=item[1], time=item[2], updated=item[3])
            h.save()

        clear_sql_led()
