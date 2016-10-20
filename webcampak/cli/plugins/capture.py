"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
#import copy

#FORMAT = "abcde %(asctime)s (%(levelname)s) %(namespace)s : %(message)s"

from webcampak.core.wpakCapture import Capture

def capture_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'capture'

        # text displayed next to the label in ``--help`` output
        description = 'Capture picture from a source'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak capture --help``
        arguments = [
            (
                ['-s', '--sourceid'],
                dict(
                    help='Source ID to capture from',
                    action='store',
                    )
            )
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Calling capture process")
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
                        
        if self.app.pargs.sourceid == None:
            self.app.log.error("Please specify a Source ID")
        else:
            try:
                capture = Capture(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid)
                capture.run()
            except Exception:
                self.app.log.fatal("Ooops! Something went terribly wrong, stack trace below:", exc_info=True)
                raise
     
def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', capture_plugin_hook)
