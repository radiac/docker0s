from .base import BaseApp


class MountedApp(BaseApp, abstract=True):
    """
    A project which is in a git repository and needs to be cloned to the server and
    mounted into the container as a service
    """

    #: Repository URL suitable for use in `git <command> <repo>` on the server
    #:
    #: Example:
    #:      repo = 'git@github.com:radiac/docker0s.git'
    repo: str
