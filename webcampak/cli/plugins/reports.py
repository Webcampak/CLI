"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook

from webcampak.core.wpakReportsDaily import reportsDaily

def reports_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'reports'

        # text displayed next to the label in ``--help`` output
        description = 'Generate webcampak reports'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak reports --help``
        arguments = [
            (
                ['-t', '--thread'],
                dict(
                    help='Start/Stop a specific XFer job thread',
                    action='store',
                    )
            )
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Daily reports for all sources")
    def daily(self):
        self.app.log.info("Starting XFer Dispatch", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        reportsDailyClass = reportsDaily(self.app.log, self.app.config, config_dir)
        reportsDailyClass.run()

def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', reports_plugin_hook)
