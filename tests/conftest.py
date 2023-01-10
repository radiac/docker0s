from __future__ import annotations

import hashlib
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from fabric.runners import Result

from docker0s import git
from docker0s import host as docker0s_host
from docker0s.host import Host
from docker0s.manifest import Manifest

from .constants import GITHUB_EXISTS_CONTENT, GITHUB_EXISTS_PARTS, HOST_NAME


@pytest.fixture
def mock_call(monkeypatch):
    """
    Mock call_or_die for local calls

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
            monkeypatch.setattr(git, "call", self)
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


@pytest.fixture()
def assert_no_calls(mock_call):
    """
    Assert the test makes no system call
    """
    with mock_call(stdout="") as mocked:
        yield
    assert mocked.stack == []


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


@pytest.fixture
def mock_fabric(monkeypatch):
    """
    Patch the fabric Connection object and track calls to run and put
    """

    @dataclass
    class RunLog:
        cmd: str
        env: dict[str, Any] | None

        def as_flat(self):
            return ("run", self.cmd, self.env)

    @dataclass
    class PutStringIO:
        data: str

    @dataclass
    class PutLog:
        source: str
        destination: str

        def as_flat(self):
            source = self.source
            if isinstance(self.source, StringIO):
                source = PutStringIO(data=self.source.read())
            return ("put", source, self.destination)

    class MockContext:
        StringIO = PutStringIO

        def __enter__(self):
            log_stack = self.log_stack = []

            class MockConnection:
                def __init__(
                    self,
                    host: str,
                    port: str | int,
                    user: str,
                    connect_kwargs: dict[str, Any] | None = None,
                    forward_agent: bool | None = None,
                ):
                    self.host = host
                    self.port = port
                    self.user = user

                @contextmanager
                def cd(self, dir: str):
                    yield

                def run(self, cmd: str, env: dict[str, Any] | None, **kwargs) -> Result:
                    log_stack.append(RunLog(cmd=cmd, env=env))
                    return Result(connection=self)

                def put(self, source: str, destination: str):
                    log_stack.append(PutLog(source=source, destination=destination))

            # Something here is screwing things up

            monkeypatch.setattr(docker0s_host, "Connection", MockConnection)

            return self

        def __exit__(self, *args):
            pass

        @property
        def flat_stack(self):
            """
            Helper for checking stack as a list of ('run', ...) and ('put', ...) tuples
            """
            return [log.as_flat() for log in self.log_stack]

    return MockContext


@pytest.fixture
def host_cls():
    """
    A sample host class
    """
    return Host.from_dict(
        name="FakeTestHost",
        path=Path(__file__).parent,
        module="docker0s.tests",
        data={"name": HOST_NAME, "port": 22, "user": "user"},
    )


@pytest.fixture
def host(host_cls):
    """
    A sample host instance
    """
    return host_cls()


@pytest.fixture
def mk_manifest(host_cls, tmp_path):
    """
    Generate a manifest for a list of apps
    """

    def factory(*app_classes) -> Manifest:
        manifest = Manifest(tmp_path / "manifest.yml")
        for app_cls in app_classes:
            manifest.add_app(app_cls)
        manifest.host = host_cls

        return manifest

    return factory
