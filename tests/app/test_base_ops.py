"""
Test the operations of app definitions - the methods which deploy and call
docker-compose on the host
"""

from pathlib import Path, PosixPath

import pytest

from docker0s.app.base import AppsTemplateContext, BaseApp, EnvTemplateContext

from ..constants import HOST_NAME


@pytest.fixture
def base_app(host):
    """
    A sample BaseApp instance

    Path is taken from module name: tests/app/
    """
    return BaseApp.from_dict(
        name="SampleApp",
        path=Path(__file__).parent,
        module="tests.app.test_base_ops",
        data=dict(
            compose="data/docker-compose.yml",
        ),
    )(host)


def test_app__remote_path(base_app):
    assert base_app.remote_path == PosixPath("/home/user/apps/sample_app")


def test_app__remote_compose(base_app):
    assert base_app.remote_compose == PosixPath(
        "/home/user/apps/sample_app/docker-compose.yml"
    )


def test_app__remote_env(base_app):
    assert base_app.remote_env == PosixPath("/home/user/apps/sample_app/env")


def test_mocked_app__deploy(mock_fabric, base_app):
    with mock_fabric() as mocked:
        base_app.deploy()

    assert mocked.flat_stack == [
        ("run", "mkdir -p /home/user/apps/sample_app", None),
        (
            "put",
            mocked.StringIO(
                'version: "3.8"\n'
                "services:\n"
                "  service1:\n"
                "    image: service1\n"
                "  service2:\n"
                "    image: service2\n"
            ),
            "/home/user/apps/sample_app/docker-compose.yml",
        ),
        (
            "put",
            mocked.StringIO(
                'COMPOSE_PROJECT_NAME="sample_app"\n'
                'ENV_FILE="/home/user/apps/sample_app/env"\n'
                'ASSETS_PATH="/home/user/apps/sample_app/assets"\n'
                'STORE_PATH="/home/user/apps/sample_app/store"'
            ),
            "/home/user/apps/sample_app/env",
        ),
    ]


def test_compose_content__template_with_context__renders(mk_manifest, tmp_path):
    template_path = tmp_path / "docker-compose.jinja2"
    template_path.write_text(
        """version: "3.8"
  services:
{% if service1 %}
    service1:
        image: service1
{% endif %}
    service2:
        image: service2
    """
    )

    class TestApp(BaseApp):
        compose = str(template_path)
        compose_context = {"service1": True}

    app = mk_manifest(TestApp).init_apps()[0]
    assert (
        app.get_compose_content()
        == """version: "3.8"
  services:

    service1:
        image: service1

    service2:
        image: service2
    """
    )


def test_compose_content__reserved_context__data_exists(mk_manifest):
    class TestApp(BaseApp):
        pass

    # Create app and manifest
    manifest = mk_manifest(TestApp)
    apps = manifest.init_apps()
    assert len(apps) == 1
    app = apps[0]

    # Collect reserved context
    context = app.get_compose_context()

    # Check host
    assert context["host"] == app.host

    # Check template context objects
    assert isinstance(context["apps"], AppsTemplateContext)
    assert isinstance(context["env"], EnvTemplateContext)

    # Check reserved words are there
    assert context["docker0s"] == NotImplemented
    assert context["globals"] == NotImplemented


def test_compose_content__reserved_context__data_renders(mk_manifest, tmp_path):
    template_path = tmp_path / "docker-compose.jinja2"
    template_path.write_text(
        "host.name={{ host.name }}"
        " apps.TestApp2.foo={{ apps.TestApp2.foo }}"
        " apps.TestApp2.baz={{ apps.TestApp2.env.baz }}"
    )

    class TestApp1(BaseApp):
        compose = str(template_path)

    class TestApp2(BaseApp):
        compose_context = {"foo": "bar"}
        env = {"baz": "qux"}

    # Create apps and sanity check
    manifest = mk_manifest(TestApp1, TestApp2)
    apps = manifest.init_apps()
    assert len(apps) == 2
    app1, app2 = apps
    assert isinstance(app1, TestApp1)
    assert isinstance(app2, TestApp2)

    assert app1.get_compose_content() == (
        f"host.name={HOST_NAME} apps.TestApp2.foo=bar apps.TestApp2.baz=qux"
    )


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
                "--file /home/user/apps/sample_app/docker-compose.yml "
                "--env-file /home/user/apps/sample_app/env "
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
                "--file /home/user/apps/sample_app/docker-compose.yml "
                "--env-file /home/user/apps/sample_app/env "
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
                "--file /home/user/apps/sample_app/docker-compose.yml "
                "--env-file /home/user/apps/sample_app/env "
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
                "--file /home/user/apps/sample_app/docker-compose.yml "
                "--env-file /home/user/apps/sample_app/env "
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
                "--file /home/user/apps/sample_app/docker-compose.yml "
                "--env-file /home/user/apps/sample_app/env "
            )
            + cmd_out,
            None,
        )
    ]
