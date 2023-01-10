"""
Test docker0s.app.app.App
"""
from pathlib import Path

import pytest

from docker0s.app.app import App


@pytest.fixture
def compose_path_yml():
    return Path(__file__).parent.parent / "data" / "docker-compose.yml"


@pytest.fixture
def app(host, compose_path_yml):
    """
    A sample App instance

    Path is taken from module name: tests/app/
    """
    return App.from_dict(
        name="SampleApp",
        path=Path(__file__).parent,
        module="tests.app.test_app",
        data={"compose": str(compose_path_yml)},
    )(host)


def test_app_is_abstract():
    assert App.abstract is True


def test_app_subclass_is_concrete():
    class TestApp(App):
        pass

    assert TestApp.abstract is False


def test_mocked_app__deploy(mock_fabric, app, compose_path_yml):
    with mock_fabric() as mocked:
        app.deploy()

    assert mocked.flat_stack == [
        ("run", "mkdir -p /home/user/apps/sample_app", None),
        (
            "put",
            mocked.StringIO(compose_path_yml.read_text()),
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
