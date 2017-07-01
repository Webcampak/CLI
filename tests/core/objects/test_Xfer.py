from unittest import TestCase
from webcampak.core.objects.wpakXfer import Xfer
from cement.core import foundation
import gettext

class TestXfer(TestCase):

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

    def test_xfer(self):
        """Initialize xfer class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

#        xfer_empty = {}

        xfer = Xfer(app.log, dir_schemas = '/home/webcampak/webcampak/resources/schemas/')
#        self.assertEqual(xfer.xfer, xfer_empty)


