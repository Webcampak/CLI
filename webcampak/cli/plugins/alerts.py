"""Example Plugin for Webcampak."""

from builtins import object
from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook

from webcampak.core.wpakAlertsCapture import alertsCapture

def alerts_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta(object):
        # name that the controller is displayed at command line
        label = 'alerts'

        # text displayed next to the label in ``--help`` output
        description = 'Trigger some alerts based on specific events or checks'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak alerts --help``
        arguments = [
            (
                ['-s', '--sourceid'],
                dict(
                    help='Run the alert only for the specified source',
                    action='store',
                    )
            )
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Alert if a capture is running late based on source schedule")
    def capture(self):
        self.app.log.info("Starting Capture Alert", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')

        try:
            start = alertsCapture(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid)
            start.run()
        except Exception:
            self.app.log.fatal("Ooops! Something went terribly wrong, stack trace below:", exc_info=True)
            raise


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', alerts_plugin_hook)
