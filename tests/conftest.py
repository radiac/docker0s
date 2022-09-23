import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from docker0s import git

from .constants import GITHUB_EXISTS_CONTENT, GITHUB_EXISTS_PARTS


@pytest.fixture
def mock_call(monkeypatch):
    """
    Usage::

        def test_call(mock_call):
            with mock_call(stdout="stdout response") as mocked:
                call_or_die('ls')
            assert mocked.stack[0].cmd = ['ls']
    """

    @dataclass
    class MockLog:
        cmd: tuple[str, ...]
        cwd: Path | None
        expected: str | None

    class MockedCall:
        def __init__(self, stdout=None):
            self.stdout = None

        def __enter__(self):
            monkeypatch.setattr(git, "call_or_die", self)
            self.stack = []
            return self

        def __exit__(self, *args):
            pass

        def __call__(
            self,
            *cmd: str,
            cwd: Path | None = None,
            expected: str | None = None,
        ) -> subprocess.CompletedProcess:
            self.stack.append(MockLog(cmd=cmd, cwd=cwd, expected=expected))
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=self.stdout)

        @property
        def cmd_cwd_stack(self):
            """
            Helper for checking cmd and cwd pairs
            """
            return [(log.cmd, log.cwd) for log in self.stack]

    return MockedCall


@pytest.fixture
def cache_path(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(git, "CACHE_PATH", tmp_path)
    return tmp_path


@pytest.fixture
def mock_file(cache_path):
    url, ref, path = GITHUB_EXISTS_PARTS
    repo_path = cache_path / hashlib.md5(url.encode()).hexdigest()
    file_path = repo_path / path
    file_path.parent.mkdir(parents=True)
    file_path.write_text(GITHUB_EXISTS_CONTENT)

    return (url, ref, path, file_path)
