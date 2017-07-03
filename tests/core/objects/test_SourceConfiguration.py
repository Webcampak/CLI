from unittest import TestCase
from webcampak.core.objects.wpakSource import Source
from webcampak.core.objects.wpakSourceConfiguration import SourceConfiguration
from webcampak.core.wpakConfigObj import Config
from cement.core import foundation
import gettext

class TestSourceConfiguration(TestCase):

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

    def test_load(self):
        """Initialize alert class and update some content"""
        # App init, necessary to get to the logging service
        self.set_gettext()
        app = self.get_app()

        config_paths = Config(app.log, '/home/webcampak/webcampak/config/param_paths.yml')

        source = Source(app.log, source_id = 1, config_paths = config_paths)
        source.cfg.get_capture_val('cfgsourceactive')
        source.cfg.get_capture_val('cfgsourcetype')
        source.cfg.get_capture_val('does_not_exist')
#        app.log.info(source)
#        app.log.info(source.cfg)
#        app.log.info(source.cfg.schema)
#        app.log.info(source.cfg.cfg)
#        app.log.info(source.cfg.get_capture_val('cfgsourceactive'))

