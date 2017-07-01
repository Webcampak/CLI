from unittest import TestCase
from webcampak.core.objects.wpakCapture import Capture
from cement.core import foundation
import gettext

class TestCapture(TestCase):

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

    def test_capture(self):
        """Initialize capture class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

        capture_empty = {'scriptStartDate': None, 'scriptEndDate': None, 'totalCaptureSize': 0, 'processedPicturesCount': 0, 'captureDate': None, 'storedJpgSize': 0, 'captureSuccess': None, 'scriptRuntime': None, 'storedRawSize': 0}

        capture = Capture(app.log, dir_schemas = '/home/webcampak/webcampak/resources/schemas/')
        self.assertEqual(capture.capture, capture_empty)


