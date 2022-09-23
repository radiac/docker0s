from __future__ import annotations

from pathlib import Path

from .manifest_object import ManifestObject
from .path import AppPath


class HostPath:
    """
    Remote path helper to ensure consistency
    """

    root: Path

    def __init__(self, root: str):
        self.root = Path(root)

    def app(self, app: str):
        return self.root / app


class Host(ManifestObject, abstract=True):
    #: Abstract base classes should be marked as abstract so they are ignored by the
    #: manifest loader
    abstract: bool = True

    #: Server hostname
    name: str

    #: Server port
    port: str | int | None

    #: Username for login
    user: str | None

    #: Path to the docker0s working dir on the server
    remote_path: str | HostPath = HostPath(root="~/.docker0s")

    def get_remote_path(self) -> HostPath:
        if isinstance(self.remote_path, HostPath):
            return self.remote_path
        return HostPath(self.remote_path)

    def call_compose(self, path: AppPath, cmd: str):
        """
        Execute a docker-compose command on the server
        """

    def push(self, source: Path | str, destination: Path | str):
        """
        Push a file to the server
        """

    def write(self, destination: Path | str, content: str):
        """
        Write a file to the server
        """
