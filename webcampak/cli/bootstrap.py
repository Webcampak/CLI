"""Webcampak bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as wpakBaseController.

from cement.core import handler
from webcampak.cli.controllers.base import wpakBaseController

def load(app):
    handler.register(wpakBaseController)
