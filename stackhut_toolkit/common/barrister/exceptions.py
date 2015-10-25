
class ConfigError(Exception):
    """
    Parent class for errors caused by bad configuration.
    """
    def __init__(self, message, *args, **kwargs):
        self.message = message

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.message)


class InvalidFunctionError(ConfigError):
    """
    Error raised when a function definition is not valid.
    """
    pass
