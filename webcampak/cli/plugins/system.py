"""Example Plugin for Webcampak."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook, foundation

from webcampak.core.wpakSystemCronJobs import systemCronJobs
from webcampak.core.wpakSystemFtpAccounts import systemFtpAccounts

def system_plugin_hook(app):
    # do something with the ``app`` object here.
    pass

class ExamplePluginController(CementBaseController):
    class Meta:
        # name that the controller is displayed at command line
        label = 'system'

        # text displayed next to the label in ``--help`` output
        description = 'Execute system level activities (requires sudo)'

        # stack this controller on-top of ``base`` (or any other controller)
        stacked_on = 'base'

        # determines whether the controller is nested, or embedded
        stacked_type = 'nested'

    @expose(hide=True)
    def default(self):
        self.app.log.info("Please indicate which command to run")

    @expose(help="Create local FTP accounts used to access sources")
    def ftp(self):
        self.app.log.info("Starting FTP Account Creation", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
            
        ftpAccounts = systemFtpAccounts(self.app.log, self.app.config, config_dir)
        ftpAccounts.create()

        
    @expose(help="Update Crontab with latest configuration values")
    def cron(self):
        self.app.log.info("Updating Crontab", __file__)
        if self.app.pargs.config_dir != None:
            config_dir = self.app.pargs.config_dir
        else:
            config_dir = self.app.config.get('webcampak', 'config_dir')
                
        cronJobs = systemCronJobs(self.app.log, self.app.config, config_dir)
        cronJobs.update()
                
def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(ExamplePluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', system_plugin_hook)
