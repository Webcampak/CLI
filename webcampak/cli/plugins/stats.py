"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook, foundation

from webcampak.core.wpakStatsCollect import statsCollect
from webcampak.core.wpakStatsConsolidate import statsConsolidate
#from webcampak.core.wpakXferStart import xferStart
#from webcampak.core.wpakXferStop import xferStop

def xfer_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'stats'

        # text displayed next to the label in ``--help`` output
        description = 'Collect and consolidate Webcampak statistics'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak stats --help``
        arguments = [
            #(
            #    ['-tbc', '--tbd'],
            #    dict(
            #        help='Start/Stop a specific XFer job thread',
            #        action='store',
            #        )
            #)
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Collect Webcampak stats")
    def collect(self):
        self.app.log.info("Starting Webcampak Stats Collection", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        collect = statsCollect(self.app.log, self.app.config, config_dir)
        collect.run()
        
    @expose(help="Consolidate Webcampak stats")
    def consolidate(self):
        self.app.log.info("Starting Webcampak Stats Consolidation", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        consolidate = statsConsolidate(self.app.log, self.app.config, config_dir)
        consolidate.run()        

def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', xfer_plugin_hook)