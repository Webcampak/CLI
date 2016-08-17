"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook, foundation

from webcampak.core.wpakVideo import Video

def video_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'video'

        # text displayed next to the label in ``--help`` output
        description = 'Handle the creation of Webcampak Videos'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

        # these arguments are only going to display under
        # ``$ webcampak video --help``
        arguments = [
            (
                ['-s', '--sourceid'],
                dict(
                    help='Source ID to generate a video for',
                    action='store',
                    )
            )
        ]

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Based on calendar days, generate Webcampak daily video.")
    def daily(self):
        self.app.log.info("Starting daily video creation", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        video = Video(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid, 'video')
        video.run()         

    @expose(help="Generate a custom video based on a specified time window")
    def custom(self):
        self.app.log.info("Starting custom video creation", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        video = Video(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid, 'videocustom')
        video.run()    
        
    @expose(help="Batch manipulate pictures in prepartion of creating a video")
    def videopost(self):
        self.app.log.info("Starting post prod maniuplations", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        video = Video(self.app.log, self.app.config, config_dir, self.app.pargs.sourceid, 'videopost')
        video.run()         
        
def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', video_plugin_hook)
