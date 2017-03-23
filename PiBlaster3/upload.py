
import os

from .mpc import MPC


class Uploader:
    """

    """

    def __init__(self):
        """

        """
        self.upload_dir = '/var/lib/mpd/music/Upload'  # TODO: config

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


