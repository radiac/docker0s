from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .exceptions import DefinitionError
from .git import fetch_repo, parse_git_url


def find_manifest(path: Path) -> Path | None:
    """
    Look within the given Path for a manifest file

    Returns the full Path to the manifest, or None if not found
    """
    files = [
        "d0s-manifest.py",
        "d0s-manifest.yml",
        "d0s-manifest.yaml",
    ]

    # Return the first which exists
    for filename in files:
        filepath = path / filename
        if filepath.exists():
            return filepath

    return None


def path_to_uuid(path: Path) -> str:
    """
    Convert a path into a UUID
    """
    hash = hashlib.md5(str(path).encode()).hexdigest()
    return f"_{hash}"


def path_to_relative(root: Path, path: Path) -> str:
    """
    Given a root path and a sub-path, return the trailing relative path
    """
    if not path.is_relative_to(root):
        raise DefinitionError(f"Path {path} is not a sub-path of {root}")
    relative = str(path)[len(str(root)) :]
    return relative.lstrip("/")


class ExtendsPath:
    """
    Path to a base manifest
    """

    #: Original ``extends`` path, or dir containing a base d0s-manifest
    original: str

    #: Current working directory - directory of the manifest which set ``extends`` - for
    #: resolving relative paths
    cwd: Path

    #: Full ``extends`` path to the manifest, or dir containing a d0s-manifest
    path: Path

    #: Git repository
    repo: str | None = None
    ref: str | None = None

    #: App name within the manifest
    name: str | None = None

    def __init__(self, path: str, cwd: Path):
        """
        Resolve the path to a local Path, retrieving a local copy if a remote source
        """
        self.original = path
        self.cwd = cwd

        if path.startswith(("git+ssh://", "git+https://")):
            # Break up URL into parts
            self.repo, self.ref, repo_rel_path, self.name = parse_git_url(path)

            # Pull and build local path
            repo_local_path = self._pull_repo()
            self.path = (repo_local_path / (repo_rel_path or "")).resolve()

            # Validate local path
            #
            # This is to catch mistakes and bad practice, not security issues - we'll
            # potentially be running Python with no attempt at sandboxing
            if not self.path.is_relative_to(repo_local_path):
                raise DefinitionError(
                    f"Invalid git URL format {path}"
                    f" - repo path {repo_rel_path} not relative to repo root"
                )
        else:
            if "::" in path:
                path, self.name = path.split("::")
            self.path = (self.cwd / path).resolve()

    def __truediv__(self, other: Any) -> Path:
        """
        Add ``other`` to this path, where ``other`` must be within this path
        """
        return (self.path / other).resolve()

    def _pull_repo(self) -> Path:
        """
        Clone local copy of repo
        """
        local_path: Path = fetch_repo(self.repo, self.ref)
        return local_path

    def get_manifest(self) -> Path:
        # If we've been given the path to the manifest file then we're already there
        if self.path.is_file():
            return self.path

        # Not found, we must have a dir to search
        if not self.path.is_dir():
            raise DefinitionError(
                f"Manifest not found at {self.path} ({self.original})"
            )

        # We'll search for these
        filepath = find_manifest(self.path)
        if filepath is None:
            raise DefinitionError(
                f"Manifest not found in {self.path} ({self.original})"
            )
        return filepath
