"""
Test the operations of app definitions - the methods which deploy and call
docker-compose on the host
"""

from pathlib import PosixPath

import pytest

from docker0s.app.base import BaseApp


@pytest.fixture
def base_app(host):
    """
    A sample BaseApp instance

    Path is taken from module name: tests/app/
    """
    return BaseApp.from_dict("SampleApp", "tests.app.test_base_ops", {})(host)


def test_app__remote_path(base_app):
    assert base_app.remote_path == PosixPath("apps/sample_app")


def test_app__remote_compose(base_app):
    assert base_app.remote_compose == PosixPath("apps/sample_app/docker-compose.yml")


def test_app__remote_env(base_app):
    assert base_app.remote_env == PosixPath("apps/sample_app/env")


def test_mocked_app__deploy(mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.deploy()

    assert mocked.flat_stack == [
        ("run", "mkdir -p apps/sample_app", None),
        (
            "put",
            mocked.StringIO('COMPOSE_PROJECT_NAME="sample_app"'),
            "apps/sample_app/env",
        ),
    ]


@pytest.mark.parametrize(
    "cmd, cmd_args, cmd_out",
    [
        ("up", {}, "up"),
        ("up {service}", {"service": "mycontainer"}, "up mycontainer"),
    ],
)
def test_mocked_app__call_compose(cmd, cmd_args, cmd_out, mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.call_compose(cmd, cmd_args)

    assert mocked.flat_stack == [
        (
            "run",
            (
                "docker-compose "
                "--file apps/sample_app/docker-compose.yml "
                "--env-file apps/sample_app/env "
            )
            + cmd_out,
            None,
        ),
    ]


@pytest.mark.parametrize(
    "services, cmds_out",
    [
        ([], ["up --build --detach"]),
        (["mycontainer"], ["up --build --detach mycontainer"]),
        (
            ["con1", "con2", "con3"],
            [
                "up --build --detach con1",
                "up --build --detach con2",
                "up --build --detach con3",
            ],
        ),
    ],
)
def test_mocked_app__call_up(services, cmds_out, mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.up(*services)

    flat_stack = mocked.flat_stack
    assert len(flat_stack) == len(cmds_out)
    for actual, expected_cmd in zip(flat_stack, cmds_out):
        assert actual == (
            "run",
            (
                "docker-compose "
                "--file apps/sample_app/docker-compose.yml "
                "--env-file apps/sample_app/env "
            )
            + expected_cmd,
            None,
        )


@pytest.mark.parametrize(
    "services, cmds_out",
    [
        ([], ["down"]),
        (["mycontainer"], ["rm --force --stop -v mycontainer"]),
        (
            ["con1", "con2", "con3"],
            [
                "rm --force --stop -v con1",
                "rm --force --stop -v con2",
                "rm --force --stop -v con3",
            ],
        ),
    ],
)
def test_mocked_app__call_down(services, cmds_out, mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.down(*services)

    flat_stack = mocked.flat_stack
    assert len(flat_stack) == len(cmds_out)
    for actual, expected_cmd in zip(flat_stack, cmds_out):
        assert actual == (
            "run",
            (
                "docker-compose "
                "--file apps/sample_app/docker-compose.yml "
                "--env-file apps/sample_app/env "
            )
            + expected_cmd,
            None,
        )


@pytest.mark.parametrize(
    "services, cmds_out",
    [
        ([], ["restart"]),
        (["mycontainer"], ["restart mycontainer"]),
        (
            ["con1", "con2", "con3"],
            [
                "restart con1",
                "restart con2",
                "restart con3",
            ],
        ),
    ],
)
def test_mocked_app__call_restart(services, cmds_out, mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.restart(*services)

    flat_stack = mocked.flat_stack
    assert len(flat_stack) == len(cmds_out)
    for actual, expected_cmd in zip(flat_stack, cmds_out):
        assert actual == (
            "run",
            (
                "docker-compose "
                "--file apps/sample_app/docker-compose.yml "
                "--env-file apps/sample_app/env "
            )
            + expected_cmd,
            None,
        )


@pytest.mark.parametrize(
    "service, cmd, cmd_out",
    [("mycontainer", "/bin/bash", "exec mycontainer /bin/bash")],
)
def test_mocked_app__call_exec(service, cmd, cmd_out, mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.exec(service, cmd)

    assert mocked.flat_stack == [
        (
            "run",
            (
                "docker-compose "
                "--file apps/sample_app/docker-compose.yml "
                "--env-file apps/sample_app/env "
            )
            + cmd_out,
            None,
        )
    ]
