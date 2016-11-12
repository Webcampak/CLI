"""Webcampak exception classes."""


class wpakError(Exception):
    """Generic errors."""

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class wpakConfigError(wpakError):
    """Config related errors."""
    pass


class wpakRuntimeError(wpakError):
    """Generic runtime errors."""
    pass


class wpakArgumentError(wpakError):
    """Argument related errors."""
    pass
