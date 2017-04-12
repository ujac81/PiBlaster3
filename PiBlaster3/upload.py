"""upload.py -- backend for upload from USB flash drive or direct file upload via browser.

"""
import os
import re
from django.conf import settings

from .mpc import MPC
from piremote.models import Upload


class Uploader:
    """Perform upload files, list USB flash drive and queue uploads.
    """

    def __init__(self):
        """Fetch settings."""
        self.upload_dir = settings.PB_UPLOAD_DIR

    def upload_file(self, uploader, name, f):
        """File upload posted to /upload

        :param uploader: some name for the upload directory (might be user name or whatever)
        :param name: filename
        :param f: file data
        :return: {status_str: 'some status string'}
        """
        up_dir = os.path.join(self.upload_dir, uploader)
        if os.path.exists(up_dir) and not os.path.isdir(up_dir):
            return {'error_str': 'Upload destination %s exists and is not a directory' % uploader}
        elif not os.path.exists(up_dir):
            os.mkdir(up_dir)

        filename = os.path.join(up_dir, name.name)
        if os.path.exists(filename):
            return {'error_str': 'Upload destination %s exists' % filename}

        with open(filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        mpc = MPC()
        mpc.update_database()

        return {'status_str': 'File %s uploaded to folder %s.' % (name.name, uploader)}

    def list_dir(self, path):
        """Browse directories in PB_UPLOAD_SOURCES for uploadable files.

        :param path: directory to list.
        :return: {dirname=path,
                  res=[['dir', dirname, path],  ...., ['file', filename, path, extension]]
                 }
        """
        path = re.sub(r"/$", '', path.replace('//', '/'))

        path_ok = False
        for item in settings.PB_UPLOAD_SOURCES:
            path_ok |= path.startswith(item)

        if path == '' or not path_ok:
            # We are on top level
            res = []
            for item in settings.PB_UPLOAD_SOURCES:
                res.append(['dir', item, ''])
            return dict(dirname='', browse=res)

        try:
            listing = os.listdir(path)
        except OSError:
            listing = []
            pass

        dirs = [d for d in listing if os.path.isdir(os.path.join(path, d))]
        files = [f for f in listing
                 if os.path.isfile(os.path.join(path, f))
                 and f.lower().endswith(settings.PB_MEDIA_EXT)]

        res = []
        for d in sorted(dirs):
            res.append(['dir', d, path])
        for f in sorted(files):
            ext = os.path.splitext(f)[1][1:].lower()
            res.append(['file', f, path, ext])

        return dict(dirname=path, browse=res)

    def add_to_uploads(self, up_list):
        """Queue items into upload table.

        Upload worker will retrieve items from this table and perform the upload.

        :return: some status string about the amount of files added for upload.
        """

        if len(up_list) == 0:
            return {'error_str': 'No files to upload'}

        added = 0
        for item in up_list:
            added += Upload.add_item(item)

        return {'status_str': '%d files added to upload queue' % added}
