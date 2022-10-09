from .base import BaseApp


class App(BaseApp, abstract=True):
    """
    A self-contained docker-compose file which deploys containers without additional
    resources
    """

    # Stub class to allow future customisation of the BaseApp which conflicts with other
    # app classes
