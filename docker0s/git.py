"""
GitHub helpers
"""
from __future__ import annotations

import hashlib
import re
import shlex
import subprocess
from functools import lru_cache
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING

from .exceptions import DefinitionError, ExecutionError
from .settings import CACHE_PATH


if TYPE_CHECKING:
    from .host import Host

GIT_SSH_PATTERN = re.compile(
    # url: git@github.com:username/repo
    r"^git\+ssh://(?:(?P<repo>.+?:.+?))"
    # ref: a tag, branch or commit
    r"(@(?P<ref>.+?))?"
    # path: a file within the repo
    r"(#(?P<path>.+?))?"
    # name: the name of the object in the manifest
    r"(::(?P<name>.+?))?$"
)
GIT_HTTPS_PATTERN = re.compile(
    # url: https://github.com/username/repo
    r"^git\+(?P<repo>https://.+?)"
    # ref: a tag, branch or commit
    r"(@(?P<ref>.+?))?"
    # path: a file within the repo
    r"(#(?P<path>.+?))?"
    # name: the name of the object in the manifest
    r"(::(?P<name>.+?))?$"
)
GIT_REMOTE_SHOW_PATTERN = re.compile(r"HEAD branch: (\S+)")


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


def call(
    *cmd: str,
    cwd: Path | None = None,
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
    return result


def call_or_die(
    *cmd: str,
    cwd: Path | None = None,
    expected: str | None = None,
) -> subprocess.CompletedProcess:
    result = call(*cmd, cwd=cwd)

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


def parse_git_url(path: str) -> tuple[str, str | None, str | None, str | None]:
    """
    Parses a git URL in the formats:

        git+ssh://url@ref#path/to/file::name
        git+https://url@ref#path/to/file::name

    and returns a tuple of (repo, ref, path, name)
    """
    if path.startswith("git+ssh://"):
        pattern = GIT_SSH_PATTERN
    elif path.startswith("git+https://"):
        pattern = GIT_HTTPS_PATTERN
    else:
        # Cannot support
        raise DefinitionError(f"Unrecognised git URL format {path}")

    # Pattern match
    matches = pattern.match(path)
    if not matches:
        raise DefinitionError(f"Unrecognised git URL format {path}")
    data = matches.groupdict()

    return (data["repo"], data["ref"], data["path"], data["name"])


def _parse_remote_show_to_head(raw: str) -> str:
    matches = GIT_REMOTE_SHOW_PATTERN.match(raw)
    if not matches:
        raise ExecutionError(
            'Command "git remote show origin" did not return a HEAD branch'
        )
    return matches.group(1)


@lru_cache()
def fetch_repo(url: str, ref: str | None) -> Path:
    # Build repo path
    repo_dir = hashlib.md5(url.encode()).hexdigest()
    repo_path = CACHE_PATH / repo_dir

    # Clone
    if not repo_path.exists():
        call_or_die("mkdir", "-p", str(repo_path))
        call_or_die("git", "init", cwd=repo_path)
        call_or_die("git", "remote", "add", "origin", url, cwd=repo_path)

    # If no ref, use remote's default branch
    if not ref:
        result = call_or_die(
            "git", "remote", "show", "origin", cwd=repo_path, expected="HEAD branch:"
        )
        ref = _parse_remote_show_to_head(result.stdout.decode())

    # Fetch the ref and check it out
    call_or_die("git", "fetch", "origin", ref, "--depth=1", cwd=repo_path)
    call_or_die("git", "checkout", ref, cwd=repo_path)

    # See if it's a branch or commit
    result = call(
        "git", "rev-parse", "--abbrev-ref", "--verify", f"{ref}@{{u}}", cwd=repo_path
    )
    if result.returncode == 0:
        # It is a branch, use reset to get to head
        call_or_die("git", "reset", "--hard", f"origin/{ref}", cwd=repo_path)

    return repo_path


def fetch_repo_on_host(host: Host, path: PosixPath | str, url: str, ref: str | None):
    # Clone
    if not host.exists(path):
        host.mkdir(path)
        host.exec("git init", cwd=path)
        host.exec("git remote add origin {url}", args={"url": url}, cwd=path)

    # If no ref, use remote's default branch
    if not ref:
        result = host.exec("git remote show origin", cwd=path)
        ref = _parse_remote_show_to_head(result.stdout)

    # Fetch the ref and check it out
    host.exec("git fetch origin {ref} --depth=1", args={"ref": ref}, cwd=path)
    host.exec("git checkout {ref}", args={"ref": ref}, cwd=path)

    # See if it's a branch or commit
    result = host.exec(
        "git rev-parse --abbrev-ref --verify {ref}@{{u}}",
        args={"ref": ref},
        cwd=path,
        can_fail=True,
    )
    if result.ok:
        # It is a branch, use reset to get to head
        host.exec("git reset --hard origin/{ref}", args={"ref": ref}, cwd=path)
