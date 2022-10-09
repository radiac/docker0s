from __future__ import annotations

import hashlib
import re
from io import TextIOWrapper
from pathlib import Path
from typing import TYPE_CHECKING

from . import git


if TYPE_CHECKING:
    from .app import BaseApp

GIT_SSH_PATTERN = re.compile(
    # url: git@github.com:username/repo
    r"^git\+ssh://(?:(?P<url>.+?:.+?))"
    # ref: a tag, branch or commit
    r"(@(?P<ref>.+?))?"
    # path: a file within the repo
    r"(#(?P<path>.+?))?$"
)
GIT_HTTPS_PATTERN = re.compile(
    # url: https://github.com/username/repo
    r"^git\+(?P<url>https://.+?)"
    # ref: a tag, branch or commit
    r"(@(?P<ref>.+?))?"
    # path: a file within the repo
    r"(#(?P<path>.+?))?$"
)


class ManifestPath:
    """
    A path in a manifest, which can be:

    * relative to the manifest's dir, eg ``traefik.env`` or
      ``../../apps/traefik/manifest.yml``
    * absolute, eg ``/etc/docker0s/apps/traefik/manifest.yml``
    * a file in a git repository in the format ``git+<protocol>://<path>@<ref>#<file>``
      where protocol is one of ``git+file``, ``git+https``, ``git+ssh``, and the ref is
      a branch, commit or tag. For example
      ``git+ssh://git@github.com:radiac/docker0s@main#apps/traefik/manifest.yml`` or
      ``git+https://github.com/radiac/docker0s@v1.0#apps/traefik/manifest.yml``

    """

    # Original full path
    original: str

    # Dir containing the manifest, for relative urls
    manifest_dir: Path

    def __init__(self, path: str | ManifestPath, manifest_dir: Path):
        if isinstance(path, ManifestPath):
            path = path.original
        self.original = path
        self.manifest_dir = manifest_dir

    def __str__(self) -> str:
        if self.is_local:
            return str(self.absolute)
        return self.original

    def __repr__(self):
        return f"<{type(self).__name__} '{self}'>"

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other)

    @property
    def path(self) -> str:
        return self.original

    @property
    def uuid(self) -> str:
        """
        Return a unique string for this path which is safe for use as a module name

        Will match another ManifestPath created with the same path, or an AppPath
        which resolves to the same path
        """
        if self.is_local:
            path = str(self.absolute)
        else:
            path = self.path

        hash = hashlib.md5(path.encode()).hexdigest()
        return f"_{hash}"

    @property
    def is_local(self):
        if self.is_git:
            return False
        return True

    @property
    def is_absolute(self):
        return Path(self.path).is_absolute()

    @property
    def is_git(self):
        if self.path.startswith(("git+ssh://", "git+https://")):
            return True
        return False

    @property
    def absolute(self):
        """
        If this is a local path, return the normalised absolute path, otherwise raise a
        ValueError
        """
        if not self.is_local:
            raise ValueError("ManifestPath.absolute only supports local URLs")
        path = self.manifest_dir / Path(self.path)
        return path.resolve()

    @property
    def parts(self):
        """
        If this is a git URL, return a dict of parts, otherwise raise a ValueError

        Parts:
            url
            ref
            path
        """
        if not self.is_git:
            raise ValueError("ManifestPath.parts only supports git URLs")

        if self.path.startswith("git+ssh://"):
            pattern = GIT_SSH_PATTERN
        elif self.path.startswith("git+https://"):
            pattern = GIT_HTTPS_PATTERN
        else:
            # Impossible unless someone has changed is_git
            raise RuntimeError("Subclass has broken git URL resolution")  # noqa

        matches = pattern.match(self.path)
        if not matches:
            raise ValueError("Unexpected git url pattern")

        data = matches.groupdict()
        if data["ref"] is None:
            data["ref"] = ""
        if data["path"] is None:
            data["path"] = ""
        return data

    @property
    def filetype(self) -> str:
        """
        Return the file type based on the filename suffix, if one is present.

        Does not necessarily match the suffix: forces to lowercase, standardises .yaml
        to .yml. Includes the leading period.
        """
        if "." not in self.path:
            return ""
        suffix = self.path.rsplit(".", 1)[1].lower()
        if suffix == "yaml":
            suffix = "yml"
        return f".{suffix}"

    def exists(self):
        if self.is_local:
            return self.absolute.exists()

        elif self.is_git:
            parts = self.parts
            return git.exists(parts["url"], parts["ref"], parts["path"])

        raise ValueError(f"Unsupported path {self.path}")

    def get_local_path(self) -> Path:
        if self.is_local:
            return self.absolute

        elif self.is_git:
            parts = self.parts
            return git.fetch_file(parts["url"], parts["ref"], parts["path"])

        raise ValueError(f"Unsupported path {self.path}")

    def read_text(self) -> str:
        """
        Read file text contents into a string
        """
        if self.is_local:
            return self.absolute.read_text()

        elif self.is_git:
            parts = self.parts
            return git.read_text(parts["url"], parts["ref"], parts["path"])

        raise ValueError(f"Unsupported path {self.path}")

    def stream_text(self) -> TextIOWrapper:
        """
        Return a stream for the file contents
        """
        if self.is_local:
            return open(self.absolute, "r")

        elif self.is_git:
            parts = self.parts
            return git.stream_text(parts["url"], parts["ref"], parts["path"])

        raise ValueError(f"Unsupported path {self.path}")


class AppPath(ManifestPath):
    """
    A ManifestPath which also supports paths relative to the App's ``path``:

    * relative to the app's path with ``app://``, eg if ``path = "../../apps/traefik"``
    then if an AppPath of ``app://docker0s.py" will look for the base manifest at
    ``../../apps/traefik/docker0s.py``

    This will apply to any ManifestPath defined on an App other than ``path``
    """

    app: type[BaseApp]
    _relative: str | None

    def __init__(
        self, path: str | ManifestPath, manifest_dir: Path, app: type[BaseApp]
    ):
        super().__init__(path, manifest_dir)
        self.app = app
        self._relative = ""

        if self.is_app:
            # Strip app:// from the start and check it's not trying to break free
            self._relative = self.original[len("app://") :]
            if not Path(self._relative).resolve().is_relative_to(Path(".").resolve()):
                raise ValueError("App path must be within the app root")

    def __str__(self) -> str:
        if self.is_app:
            return str(self.path)
        return super().__str__()

    @property
    def relative(self) -> str:
        """
        Relative path
        """
        if self._relative is None:
            raise ValueError("Not an app:// URL")

        return self._relative

    @property
    def path(self) -> str:
        if not self.is_app:
            return self.original

        app_path = self.app.get_path()

        if app_path.is_local:
            path = Path(app_path.original) / self.relative
            return str(path)

        elif app_path.is_git:
            original = str(app_path.original)
            root: str
            file_path: str
            if "#" in original:
                root, file_path = original.split("#", 1)
            else:
                root = original
                file_path = ""

            if file_path:
                new_path = str(Path(file_path) / self.relative)
            else:
                new_path = self.relative
            return f"{root}#{new_path}"

        raise ValueError(f"Unsupported path {self.original}")

    @property
    def is_app(self):
        if self.original.startswith("app://"):
            return True
        return False
