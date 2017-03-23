
import os
from django.conf import settings

from .mpc import MPC
from piremote.models import Upload


class Uploader:
    """

    """

    def __init__(self):
        """

        """
        self.upload_dir = settings.PB_UPLOAD_DIR

    def upload_file(self, uploader, name, f):
        """

        :param uploader:
        :param f:
        :return:
        """
        up_dir = os.path.join(self.upload_dir, uploader)
        if os.path.exists(up_dir) and not os.path.isdir(up_dir):
            return {'error': 'Upload destination %s exists and is not a directory' % uploader}
        elif not os.path.exists(up_dir):
            os.mkdir(up_dir)

        filename = os.path.join(up_dir, name.name)
        if os.path.exists(filename):
            return {'error': 'Upload destination %s exists' % filename}

        with open(filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        mpc = MPC()
        mpc.update_database()

        return {'status': 'File %s uploaded to folder %s.' % (name, uploader)}

    def list_dir(self, path):
        """

        :param path:
        :return:
        """
        path = path.replace('//', '/')

        if path == '':
            res = []
            for item in settings.PB_UPLOAD_SOURCES:
                res.append(['dir', item, ''])
            return res

        try:
            listing = os.listdir(path)
        except OSError:
            listing = []
            pass

        dirs = [d for d in listing if os.path.isdir(os.path.join(path, d))]
        files = [f for f in listing
                 if os.path.isfile(os.path.join(path, f))
                 and f.endswith(('.mp3', '.flac', '.ogg', '.wma', '.wav'))]

        res = []
        for d in sorted(dirs):
            res.append(['dir', d, path])
        for f in sorted(files):
            ext = os.path.splitext(f)[1][1:].lower()
            res.append(['file', f, path, ext])

        return res

    def add_to_uploads(self, up_list):
        """

        :return:
        """

        if len(up_list) == 0:
            return {'error': 'No files to upload'}

        added = 0
        for item in up_list:
            added += Upload.add_item(item)

        return {'status': '%d files added to upload queue' % added}
