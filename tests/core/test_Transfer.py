from unittest import TestCase
from webcampak.core.wpakTransfer import Transfer
from webcampak.core.objects.wpakSource import Source
from webcampak.core.wpakConfigObj import Config
from cement.core import foundation
import gettext
from datetime import datetime


class TestTransfer(TestCase):

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

    def test_file(self):
        """Test the function handling transfer of files"""

        self.set_gettext()
        app = self.get_app()

        config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')
        source = Source(app.log, source_id = 1, config_paths = config_paths)

        transfer = Transfer(app.log, source = source, config_paths = config_paths)
        transfer.transfer_file(datetime.now(), '/tmp/thisisatest.txt', 'abc/thisisatest.txt', 1, 3)



