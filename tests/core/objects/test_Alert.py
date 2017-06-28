from unittest import TestCase
from webcampak.core.objects.wpakAlert import Alert
from cement.core import foundation
import gettext

class TestAlert(TestCase):

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

    def test_alert(self):
        """Initialize alert class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

        alert_empty = {}

        alert = Alert(app.log, dir_schemas = '/tmp/')
        self.assertEqual(alert.alert, alert_empty)


