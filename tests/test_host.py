from pathlib import Path, PosixPath

import pytest


@pytest.mark.parametrize(
    "path, cmd_expected",
    [
        ("foo", "mkdir -p foo"),
        ("foo/bar", "mkdir -p foo/bar"),
        ('foo"bar', "mkdir -p 'foo\"bar'"),
    ],
)
def test_mocked_host__mkdir__expected(path, cmd_expected, mock_fabric, host):
    with mock_fabric() as mocked:
        host.mkdir(path)

    assert mocked.flat_stack == [
        ("run", cmd_expected, None),
    ]


@pytest.mark.parametrize(
    "path, cmd_expected",
    [
        ("foo", "mkdir -p ."),
        ("foo/bar", "mkdir -p foo"),
        ("foo/bar/what.yml", "mkdir -p foo/bar"),
    ],
)
def test_mocked_host__ensure_parent_path__expected(
    path, cmd_expected, mock_fabric, host
):
    with mock_fabric() as mocked:
        host.ensure_parent_path(PosixPath(path))

    assert mocked.flat_stack == [
        ("run", cmd_expected, None),
    ]


@pytest.mark.parametrize(
    "cmd, args, cmd_expected",
    [
        ("ls", None, "ls"),
        ("ls {path}", {"path": "/foo/bar"}, "ls /foo/bar"),
    ],
)
def test_mocked_host__exec__expected(cmd, args, cmd_expected, mock_fabric, host):
    with mock_fabric() as mocked:
        host.exec(cmd, args)

    assert mocked.flat_stack == [
        ("run", cmd_expected, None),
    ]


@pytest.mark.parametrize(
    "cmd, env",
    [
        ("ls", None),
        ("ls", {"PATH": "/foo/bar"}),
    ],
)
def test_mocked_host__exec_with_env__expected(cmd, env, mock_fabric, host):
    with mock_fabric() as mocked:
        host.exec(cmd, args=None, env=env)

    assert mocked.flat_stack == [
        ("run", cmd, env),
    ]


def test_mocked_host__call_compose(mock_fabric, host):
    with mock_fabric() as mocked:
        host.call_compose(
            compose=PosixPath("project/docker-compose.yml"),
            env=PosixPath("project/env"),
            cmd="up mycontainer",
        )

    assert mocked.flat_stack == [
        (
            "run",
            (
                "docker-compose "
                "--file project/docker-compose.yml "
                "--env-file project/env "
                "up mycontainer"
            ),
            None,
        ),
    ]


def test_mocked_host__call_compose_with_args(mock_fabric, host):
    with mock_fabric() as mocked:
        host.call_compose(
            compose=PosixPath("project/docker-compose.yml"),
            env=PosixPath("project/env"),
            cmd="up {service}",
            cmd_args={"service": "mycontainer"},
        )

    assert mocked.flat_stack == [
        (
            "run",
            (
                "docker-compose "
                "--file project/docker-compose.yml "
                "--env-file project/env "
                "up mycontainer"
            ),
            None,
        ),
    ]


def test_mocked_host__push(mock_fabric, host):
    with mock_fabric() as mocked:
        host.push(
            source=Path("local/file"),
            destination=PosixPath("remote/file"),
        )

    assert mocked.flat_stack == [
        ("run", "mkdir -p remote", None),
        ("put", "local/file", "remote/file"),
    ]


def test_mocked_host__write(mock_fabric, host):
    content = "example content"
    with mock_fabric() as mocked:
        host.write(
            filename=PosixPath("remote/file"),
            content=content,
        )

    assert mocked.flat_stack == [
        ("run", "mkdir -p remote", None),
        ("put", mocked.StringIO(content), "remote/file"),
    ]
