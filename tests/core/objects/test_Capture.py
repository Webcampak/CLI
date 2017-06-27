from unittest import TestCase
from webcampak.core.objects.wpakCapture import Capture
import mock
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

    @mock.patch('webcampak.core.wpakConfigObj')
    def test_email(self, mock_config):
        """Initialize capture class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()
        mock_config.getConfig = mock.MagicMock(return_value={
            'dir_emails': '/tmp/email_dir/'
            , 'dir_schemas': '/tmp/schema_dir'
        })

        capture_empty = {'scriptStartDate': None, 'scriptEndDate': None, 'totalCaptureSize': 0, 'processedPicturesCount': 0, 'captureDate': None, 'storedJpgSize': 0, 'captureSuccess': None, 'scriptRuntime': None, 'storedRawSize': 0}

        capture = Capture(app.log, mock_config)
        self.assertEqual(capture.capture, capture_empty)



        # email_empty = {'status': 'queued', 'content': {'BODY': None, 'FROM': [], 'ATTACHMENTS': [], 'CC': [], 'TO': [], 'SUBJECT': None}, 'hash': None, 'logs': []}
        # self.assertEqual(email.email, email_empty)
        #
        # email_updated = {'status': 'queued', 'content': {'BODY': 'A body', 'FROM': [], 'ATTACHMENTS': [], 'CC': [], 'TO': [{'name': 'TO NAME', 'email': 'TO@EMAIL.COM'}], 'SUBJECT': 'A subject'}, 'hash': None, 'logs': []}
        # email.subject = 'A subject'
        # email.body = 'A body'
        # email.field_to.append({'name': 'TO NAME', 'email': 'TO@EMAIL.COM'})
        # self.assertEqual(email.email, email_updated)


