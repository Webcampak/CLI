from unittest import TestCase
from webcampak.core.utils.wpakFTPTransfer import FTP_Transfer
from webcampak.core.objects.wpakSource import Source
from webcampak.core.wpakConfigObj import Config
import gettext
from cement.core import foundation

class TestFTPTransfer(TestCase):

    @classmethod
    def set_gettext(self):
        t = gettext.translation('webcampak', '/home/webcampak/webcampak/i18n/sds/', ['en_US.utf8'], fallback=True)
        _ = t.ugettext
        t.install()

    @classmethod
    def get_app(self):
        """App init, necessary to get to the logging service"""
        app = foundation.CementApp('myapp')
        app.setup()
        app.run()
        return app

    def test_put(self):
        """This function tests the submission of a file to a remote FTP Server"""
        #TODO: Re-enable
        # self.set_gettext()
        # app = self.get_app()
        #
        # config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')
        # source = Source(app.log, source_id = 1, config_paths = config_paths)
        #
        # currentFTP = FTP_Transfer(app.log, config_paths=config_paths, ftp_server=source.servers[1])
        #
        # self.assertEqual(currentFTP.connect(), True)
        # self.assertEqual(currentFTP.put('/tmp/thisisatest.txt', 'abc/test_FTPTransfer.txt'), True)
        # self.assertEqual(currentFTP.close(), True)

    def test_get(self):
        """This function tests the download of a file to a remote FTP Server"""

        #TODO: Re-enable
        #
        # self.set_gettext()
        # app = self.get_app()
        #
        # config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')
        # source = Source(app.log, source_id = 1, config_paths = config_paths)
        #
        # currentFTP = FTP_Transfer(app.log, config_paths=config_paths, ftp_server=source.servers[1])
        #
        # self.assertEqual(currentFTP.connect(), True)
        # self.assertEqual(currentFTP.get('/tmp/downloaded_file.txt', 'abc/test_FTPTransfer.txt'), True)
        # self.assertEqual(currentFTP.close(), True)