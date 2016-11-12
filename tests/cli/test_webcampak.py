"""CLI tests for webcampak."""

from webcampak.utils import test

class CliTestCase(test.wpakTestCase):
    def test_webcampak_cli(self):
        self.app.setup()
        self.app.run()
        self.app.close()
