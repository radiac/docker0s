from pathlib import Path, PosixPath

from ..exceptions import DefinitionError
from ..git import fetch_repo_on_host, parse_git_url
from .base import BaseApp


# Remote dir name to clone the repo
REPO_DIR = "repo"


class RepoApp(BaseApp, abstract=True):
    """
    A project which is in a git repository and needs to be cloned to the server and
    mounted into the container as a service

    The ``repo`` must be a ``git+`` repository URL.
    """

    #: ``git+`` URL for the repository to deploy
    repo: str | None = None

    #: Relative path to the compose file within the repository.
    #:
    #: If this path exists, Docker0s will overwrite this file with the ``compose`` file.
    #:
    #: See docs for recommended configuration
    #:
    #: Default: docker-compose.docker0s.yml
    repo_compose: str = "docker-compose.docker0s.yml"

    @classmethod
    def get_repo(cls) -> str:
        """
        Validate repo argument
        """
        if not cls.repo or not cls.repo.startswith(("git+ssh://", "git+https://")):
            raise DefinitionError("RepoApp must set a valid git URL in repo")
        return cls.repo

    @property
    def remote_repo_path(self) -> PosixPath:
        return self.remote_path / REPO_DIR

    @property
    def remote_compose(self) -> PosixPath:
        """
        A PosixPath to the remote compose file
        """
        _: Path
        compose_filename: str = self.repo_compose
        remote_path: PosixPath = self.remote_repo_path / compose_filename
        return remote_path

    def deploy(self):
        self.clone_on_host()
        super().deploy()

    def clone_on_host(self):
        """
        Clone or update the repository on the host
        """
        self.host.ensure_parent_path(self.remote_repo_path)

        # Break up URL into parts
        url, ref, repo_rel_path, name = parse_git_url(self.get_repo())
        if repo_rel_path or name:
            raise DefinitionError(
                f'Invalid setting "{self.get_name()}.repo": Cannot clone a'
                " repository with a relative path or name"
            )
        fetch_repo_on_host(host=self.host, path=self.remote_repo_path, url=url, ref=ref)
