"""Webcampak main application entry point."""
from __future__ import print_function

from builtins import object
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.exc import FrameworkError, CaughtSignal
from webcampak.core import exc

# Application default.  Should update config/webcampak.conf to reflect any
# changes, or additions here.
defaults = init_defaults('webcampak')

# All internal/external plugin configurations are loaded from here
#defaults['webcampak']['plugin_config_dir'] = '/etc/webcampak/plugins.d'
defaults['webcampak']['plugin_config_dir'] = '/home/webcampak/webcampak/apps/cli/config/plugins.d'

# External plugins (generally, do not ship with application code)
defaults['webcampak']['plugin_dir'] = '/var/lib/webcampak/plugins'

# External templates (generally, do not ship with application code)
defaults['webcampak']['template_dir'] = '/var/lib/webcampak/templates'

# Default place where webcampak configuration is being stored
defaults['webcampak']['config_dir'] = '/home/webcampak/webcampak/config/'


class wpakApp(CementApp):
    class Meta(object):
        label = 'webcampak'
        config_defaults = defaults

        # All built-in application bootstrapping (always run)
        bootstrap = 'webcampak.cli.bootstrap'

        # Internal plugins (ship with application code)
        plugin_bootstrap = 'webcampak.cli.plugins'

        # Internal templates (ship with application code)
        template_module = 'webcampak.cli.templates'


class wpakTestApp(wpakApp):
    """A test app that is better suited for testing."""
    class Meta(object):
        # default argv to empty (don't use sys.argv)
        argv = []

        # don't look for config files (could break tests)
        config_files = []

        # don't call sys.exit() when app.close() is called in tests
        exit_on_close = False


# Define the applicaiton object outside of main, as some libraries might wish
# to import it as a global (rather than passing it into another class/func)
app = wpakApp()

def main():
    with app:
        # add any arguments after setup(), and before run()
        app.args.add_argument('-c', '--config', action='store', dest='config_dir',
                          help='Webcampak configuration directory')

        #app.args.add_argument('-t', '--thread', action='store', dest='thread_uuid',
        #              help='Start/Stop a specific XFer job thread')                      
                      
        app.log.info("--------------------------", __file__)                      
        app.log.info("| Starting Webcampak CLI |", __file__)                      
        app.log.info("--------------------------", __file__)                      
        try:
            app.run()
        
        except exc.wpakError as e:
            # Catch our application errors and exit 1 (error)
            print('wpakError > %s' % e)
            app.exit_code = 1
            
        except FrameworkError as e:
            # Catch framework errors and exit 1 (error)
            print('FrameworkError > %s' % e)
            app.exit_code = 1
            
        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('CaughtSignal > %s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
