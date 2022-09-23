from .base import BaseApp


class App(BaseApp, abstract=True):
    """
    A self-contained docker-compose file which deploys containers without additional
    resources
    """
