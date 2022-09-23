from pathlib import Path
from typing import cast

import pytest

from docker0s.app.base import BaseApp
from docker0s.path import AppPath, ManifestPath

from ..constants import GITHUB_EXISTS


manifest_dir = Path("/else/where")


@pytest.fixture
def mk_mock_app():
    def mk(path: str):
        class App:
            def get_path(self):
                return ManifestPath(path, manifest_dir=Path("/foo/bar"))

        app = cast(BaseApp, App())
        return app

    return mk


@pytest.mark.parametrize(
    "invalid_path",
    [
        "app://../invalid",
        "app:///also/invalid",
    ],
)
def test_init__invalid__valueerror(invalid_path, mk_mock_app):
    app = mk_mock_app("/foo/bar")
    with pytest.raises(ValueError, match="App path must be within the app root"):
        _ = AppPath(invalid_path, manifest_dir=manifest_dir, app=app)


def test_is_app__is_app__true(mk_mock_app):
    app = mk_mock_app("/foo/bar")
    test_path = AppPath("app://test", manifest_dir=manifest_dir, app=app)
    assert test_path.is_app is True


@pytest.mark.parametrize("test_path", ["test", "/test", GITHUB_EXISTS])
def test_is_app__is_not_app__false(test_path, mk_mock_app):
    app = mk_mock_app("/foo/bar")
    test_path = AppPath(test_path, manifest_dir=manifest_dir, app=app)
    assert test_path.is_app is False


@pytest.mark.parametrize(
    "app_path, original_path, expected_path",
    [
        ("/foo/bar", "app://this/that", "/foo/bar/this/that"),
        ("foo/bar", "app://this/that", "foo/bar/this/that"),
        ("../foo/bar", "app://this/that", "../foo/bar/this/that"),
        (
            "git+ssh://git@github.com:radiac/docker0s@main",
            "app://manifest.yml",
            "git+ssh://git@github.com:radiac/docker0s@main#manifest.yml",
        ),
        (
            "git+ssh://git@github.com:radiac/docker0s@main#apps/traefik",
            "app://manifest.yml",
            "git+ssh://git@github.com:radiac/docker0s@main#apps/traefik/manifest.yml",
        ),
    ],
)
def test_path__valid__created(app_path, original_path, expected_path, mk_mock_app):
    app = mk_mock_app(app_path)
    test_path = AppPath(original_path, manifest_dir=manifest_dir, app=app)
    assert test_path.path == expected_path
