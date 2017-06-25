"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
import gettext

from webcampak.core.wpakConfigObj import Config
from webcampak.core.wpakPhidgetsUtils import phidgetsUtils

def phidgets_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'phidgets'

        # text displayed next to the label in ``--help`` output
        description = 'Performs different operations on phidget boards'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak phidgets --help``
        arguments = [
            (
                ['-s', '--sourceid'],
                dict(
                    help='Source ID of the source to operate on',
                    action='store',
                    )
            )
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Power-cycle the camera")
    def reboot(self):
        self.app.log.info("Powercycling camera", __file__)
        if self.app.pargs.config_dir != None:
            self.config_dir = self.app.pargs.config_dir
        else:
            self.config_dir = self.app.config.get('webcampak', 'config_dir')

            # capture = Capture(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid)
            # capture.run()
        if self.app.pargs.sourceid == None:
            self.app.log.error("Please specify a Source ID")
        else:
            self.log = self.app.log
            self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')
            self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
            self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
            self.dirBin = self.configPaths.getConfig('parameters')['dir_bin']
            self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']

            self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
            self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(self.app.pargs.sourceid) + '.cfg')

            try:
                t = gettext.translation(self.configGeneral.getConfig('cfggettextdomain'), self.dirLocale, [self.configGeneral.getConfig('cfgsystemlang')], fallback=True)
                _ = t.ugettext
                t.install()
                self.log.info("capture.initGetText(): " + _(
                    "Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                              % {'cfggettextdomain': self.configGeneral.getConfig('cfggettextdomain'), 'cfgsystemlang': self.configGeneral.getConfig('cfgsystemlang'),
                                 'dirLocale': self.dirLocale})
            except:
                self.log.error("No translation file available")


            self.phidgetsUtils = phidgetsUtils(self)
            self.phidgetsUtils.restartCamera()

def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', phidgets_plugin_hook)
