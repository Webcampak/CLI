"""Tests for Example Plugin."""

from webcampak.utils import test

class ExamplePluginTestCase(test.wpakTestCase):
    def test_load_example_plugin(self):
        self.app.setup()
        self.app.plugin.load_plugin('example')
