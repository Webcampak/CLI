"""Testing utilities for Webcampak."""

from webcampak.cli.main import wpakTestApp
from cement.utils.test import *

class wpakTestCase(CementTestCase):
    app_class = wpakTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(wpakTestCase, self).setUp()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(wpakTestCase, self).tearDown()

