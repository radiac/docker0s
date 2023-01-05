class Docker0sException(Exception):
    pass


class DefinitionError(Docker0sException):
    """
    A problem in the manifest definition syntax or logic
    """

    pass


class UsageError(Docker0sException):
    """
    A problem in how the app has been used
    """

    pass


class ExecutionError(Docker0sException):
    """
    A problem when trying to perform an action
    """

    pass
