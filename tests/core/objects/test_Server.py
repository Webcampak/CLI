from unittest import TestCase
from webcampak.core.objects.wpakServer import Server
from webcampak.core.wpakConfigObj import Config
from cement.core import foundation
import gettext

class TestServer(TestCase):

    def test_init(self):
        """Initialize server object and init content and test"""

        test_server = {
            'id': 1
            , 'name': 'Server Name'
            , 'host': 'Remote Host'
            , 'username': 'Username'
            , 'password': 'Password'
            , 'directory': '/tmp/directory/'
            , 'ftp_active': False
            , 'xfer_enable': True
            , 'xfer_threads': 0
        }

        server = Server()
        server.id = test_server['id']
        server.name = test_server['name']
        server.host = test_server['host']
        server.username = test_server['username']
        server.password = test_server['password']
        server.directory = test_server['directory']
        server.ftp_active = test_server['ftp_active']
        server.xfer_enable = test_server['xfer_enable']
        server.xfer_threads = test_server['xfer_threads']

        self.assertEqual(test_server, server.export())


