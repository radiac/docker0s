"""
GitHub helpers
"""
from __future__ import annotations

import hashlib
import shlex
import subprocess
from functools import lru_cache
from io import TextIOWrapper
from pathlib import Path

from .settings import CACHE_PATH


class CommandError(ValueError):
    def __init__(
        self,
        *args,
        cwd: Path | None = None,
        result: subprocess.CompletedProcess | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.cwd = cwd
        self.result = result

    def __str__(self):
        msg = f"{self.args[0]}\n  cwd={self.cwd}"
        if self.result:
            msg += (
                f"\n  returncode={self.result.returncode}"
                f"\n  stdout={self.result.stdout.decode()}"
                f"\n  stderr={self.result.stderr.decode()}"
            )
        return msg


def call_or_die(
    *cmd: str,
    cwd: Path | None = None,
    expected: str | None = None,
) -> subprocess.CompletedProcess:
    # This specific invocation will allow git to use the system's ssh agent
    result = subprocess.run(
        shlex.join(cmd),
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        start_new_session=True,
    )

    if result.returncode != 0:
        raise CommandError(
            f"Command failed with exit code {result.returncode}",
            cwd=cwd,
            result=result,
        )

    if expected and expected not in result.stdout.decode():
        raise CommandError(
            "Command failed with unexpected output",
            cwd=cwd,
            result=result,
        )
    return result


@lru_cache()
def fetch_repo(url: str, ref: str) -> Path:
    # Build repo path
    repo_dir = hashlib.md5(url.encode()).hexdigest()
    repo_path = CACHE_PATH / repo_dir

    # Clone
    if not repo_path.exists():
        call_or_die("mkdir", "-p", str(repo_path))
        call_or_die("git", "init", cwd=repo_path)
        call_or_die("git", "remote", "add", "origin", url, cwd=repo_path)

    # Pull
    call_or_die("git", "fetch", "origin", ref, "--depth=1", cwd=repo_path)
    call_or_die("git", "checkout", ref, cwd=repo_path)

    return repo_path


def fetch_file(url: str, ref: str, path: str) -> Path:
    """
    Fetch a repo then return a path to a file within it - regardless of whether the file
    exists or not.
    """
    if not path:
        raise ValueError("Must specify a path to read")

    repo_path: Path = fetch_repo(url, ref)
    if path.startswith("/"):
        path = path[1:]
    file_path = (repo_path / path).resolve()
    if not file_path.is_relative_to(repo_path):
        raise ValueError(f"Invalid path {path}")

    return file_path


def read_text(url: str, ref: str, path: str) -> str:
    """
    Read a file and return a string
    """
    file_path = fetch_file(url, ref, path)
    return file_path.read_text()


def stream_text(url: str, ref: str, path: str) -> TextIOWrapper:
    """
    Open a file and return an IO object
    """
    file_path = fetch_file(url, ref, path)
    return open(file_path)


def exists(url: str, ref: str, path: str) -> bool:
    """
    Check whether the file exists
    """
    file_path = fetch_file(url, ref, path)
    return file_path.exists()
