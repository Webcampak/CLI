from unittest import TestCase
from webcampak.core.utils.wpakFile import File
import mock
from cement.core import foundation

class TestClear(TestCase):

    def test_check_filepath(self):
        """This is a dummy test, only verifies that the function exists and return True"""
        filepath = '/tmp/testfile'
        self.assertEqual(File.check_filepath('/tmp/testfile'), filepath)

