"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook

from webcampak.core.wpakXferDispatch import xferDispatch
from webcampak.core.wpakXferStart import xferStart
from webcampak.core.wpakXferStop import xferStop
from webcampak.core.wpakXferClear import xferClear

def xfer_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'xfer'

        # text displayed next to the label in ``--help`` output
        description = 'Handle dispatch, processing and management of XFer jobs'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak xfer --help``
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

    @expose(help="Dispatch XFer jobs to the queue")
    def dispatch(self):
        self.app.log.info("Starting XFer Dispatch", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        dispatch = xferDispatch(self.app.log, self.app.config, config_dir)
        dispatch.run()

        
    @expose(help="Start XFer jobs queue processing")
    def start(self):
        self.app.log.info("Starting XFer Jobs", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
                
        start = xferStart(self.app.log, self.app.config, config_dir, self.app.pargs.thread)
        start.run()
        
    @expose(help="Stop XFer jobs queue processing")
    def stop(self):
        self.app.log.info("Stopping XFer Jobs", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
                
        stop = xferStop(self.app.log, self.app.config, config_dir, self.app.pargs.thread)
        stop.run()
        
    @expose(help="Stop XFer jobs and clear queue")
    def clear(self):
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')

        self.app.log.info("Stopping XFer Jobs", __file__)                
        stop = xferStop(self.app.log, self.app.config, config_dir, self.app.pargs.thread)
        stop.run()   
        self.app.log.info("Clearing XFer Jobs Queue", __file__)                
        clearQueue = xferClear(self.app.log, self.app.config, config_dir, self.app.pargs.thread)
        clearQueue.run()          
              
        
def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', xfer_plugin_hook)
