"""
Test docker0s.app.app.App
"""
from pathlib import Path

import pytest

from docker0s.app.app import App


@pytest.fixture
def app(host):
    """
    A sample App instance

    Path is taken from module name: tests/app/
    """
    return App.from_dict("SampleApp", "tests.app.test_app", {})(host)


def test_app_is_abstract():
    assert App.abstract is True


def test_app_subclass_is_concrete():
    class TestApp(App):
        pass

    assert TestApp.abstract is False


def test_mocked_app__deploy(mock_fabric, app):
    with mock_fabric() as mocked:
        app.deploy()

    assert mocked.flat_stack == [
        ("run", "mkdir -p apps/sample_app", None),
        (
            "put",
            mocked.StringIO('COMPOSE_PROJECT_NAME="sample_app"'),
            "apps/sample_app/env",
        ),
        ("run", "mkdir -p apps/sample_app", None),
        (
            "put",
            str(Path("tests/app/docker-compose.yml").resolve()),
            "apps/sample_app/docker-compose.yml",
        ),
    ]
