from pathlib import PosixPath

from ..path import AppPath, ManifestPath
from .base import BaseApp


# Remote dir name to clone the repo
REPO_DIR = "repo"


class MountedApp(BaseApp, abstract=True):
    """
    A project which is in a git repository and needs to be cloned to the server and
    mounted into the container as a service

    The path must be a ``git+`` repository URL, and the compose file must be an
    ``app://`` path within that repository"
    """

    # Redefine attributes for the benefit of docs

    #: Path to the directory containing the app. Must be a ``git+`` repository URL
    path: str = ""

    #: Filename for docker-compose definition. Must be an ``app://`` repository URL
    compose: str = BaseApp.compose

    @classmethod
    def get_path(cls) -> ManifestPath:
        path = super().get_path()
        if not path.is_git:
            raise ValueError("A MountedApp must specify a git repository as its path")
        return path

    @classmethod
    def get_compose(cls) -> AppPath:
        compose = super().get_compose()
        if not compose.is_app:
            raise ValueError("A MountedApp must specify an app:// path for its compose")

        return compose

    @property
    def remote_repo(self) -> PosixPath:
        return self.remote_path / REPO_DIR

    @property
    def remote_compose(self) -> PosixPath:
        """
        A PosixPath to the remote compose file
        """
        return self.remote_repo / self.get_compose().relative

    def deploy(self):
        super().deploy()
        self.clone_on_host()

    def push_compose_to_host(self):
        """
        Compose is within the git repository, nothing to push
        """
        return

    def push_assets_to_host(self):
        """
        Assets are within the git repository, nothing to push
        """
        return

    def clone_on_host(self):
        """
        Clone the repository on the host
        """
        self.host.ensure_parent_path(self.remote_repo)
        self.host.exec(
            "git clone {repo} {remote}",
            args={"repo": self.get_path(), "remote": self.remote_repo},
        )
