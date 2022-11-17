from pathlib import PosixPath

from ..path import ManifestPath
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
    compose: str | None = BaseApp.compose

    @classmethod
    def get_path(cls) -> ManifestPath:
        path = super().get_path()
        if not path.is_git:
            raise ValueError("A MountedApp must specify a git repository as its path")
        return path

    @property
    def remote_repo(self) -> PosixPath:
        return self.remote_path / REPO_DIR

    @property
    def remote_compose(self) -> PosixPath:
        """
        A PosixPath to the remote compose file
        """
        compose_path = self.get_compose_path()
        path: PosixPath = self.remote_repo / self.get_compose_path().relative
        if compose_path.filetype == ".jinja2":
            path = path.with_suffix(".yml")
        return path

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
