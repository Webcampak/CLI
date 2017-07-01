from unittest import TestCase
from webcampak.core.objects.wpakSource import Source
from webcampak.core.wpakConfigObj import Config
from cement.core import foundation
import gettext

class TestSource(TestCase):

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

    def test_init(self):
        """Initialize alert class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

        config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')

        source = Source(app.log, source_id = 1, config_paths = config_paths)
        self.assertEqual(source.id, 1)

    def test_load_servers(self):
        """Load servers from configuration file"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

        config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')

        source = Source(app.log, source_id = 1, config_paths = config_paths)
        source.load_servers()
        #self.assertEqual(source.id, 1)

