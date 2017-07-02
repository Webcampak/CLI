from unittest import TestCase
from webcampak.core.utils.wpakFTPTransfer import FTP_Transfer
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

        self.set_gettext()
        app = self.get_app()

        app.log.info('To be implemented')
