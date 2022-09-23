from pathlib import Path

import pytest

from docker0s import App, Host
from docker0s.app.base import BaseApp, app_registry
from docker0s.manifest import Manifest
from docker0s.path import ManifestPath


@pytest.fixture
def BaseTestApp():
    class BaseTestApp(App, abstract=True):
        """
        Define abstract base class for manifest.yml
        """

        test_id: str

    yield BaseTestApp
    del app_registry["BaseTestApp"]


def test_manifest__load_py__loads_py():
    """
    Manifest TestApp extends first.py::TestApp, which extends second.py::TestApp
    """
    path = ManifestPath("manifest.py", manifest_dir=Path(__file__) / "../data")
    manifest = Manifest.load(path)

    # Should have two apps and one host
    assert len(manifest.apps) == 2
    TestApp: App = manifest.get_app("TestApp")
    OtherApp: App = manifest.get_app("OtherApp")
    VagrantHost: Host = manifest.host

    # TestApp Should have test ID of the manifest
    assert TestApp is not None
    assert issubclass(TestApp, App)
    assert TestApp.test_id == "manifest"
    assert TestApp.get_path() == ManifestPath(
        "", manifest_dir=(Path(__file__) / "../data")
    )

    # Confirm extends works as per
    # tests/test_base_def.py:test_apply_base_manifest__extends__merges_base_classes

    # Should have first as the first base
    assert len(TestApp.__bases__) == 2
    assert TestApp.__bases__[0].test_id == "first"  # type: ignore
    assert TestApp.__bases__[1] is App

    # First should have second as first base
    assert len(TestApp.__bases__[0].__bases__) == 2
    assert TestApp.__bases__[0].__bases__[0].test_id == "second"  # type: ignore
    assert TestApp.__bases__[0].__bases__[1] is BaseApp

    # And inheritance order should give these values
    assert TestApp.compose == "first"
    assert TestApp.env_file == "second"

    # OtherApp should exist
    assert issubclass(OtherApp, App)
    assert OtherApp.path == "other_app"

    # Host
    assert issubclass(VagrantHost, Host)
    assert VagrantHost.name == "localhost"
    assert VagrantHost.port == 2222
    assert VagrantHost.user == "vagrant"


def test_manifest__load_yml__loads_yml(BaseTestApp):
    """
    Manifest TestApp extends first.py::TestApp, which extends second.py::TestApp

    Uses custom base class for internal_id
    """
    path = ManifestPath("manifest.yml", manifest_dir=Path(__file__) / "../data")
    manifest = Manifest.load(path)

    # Should have two apps and one host
    assert len(manifest.apps) == 2
    TestApp: App = manifest.get_app("TestApp")
    OtherApp: App = manifest.get_app("OtherApp")
    VagrantHost: Host = manifest.host

    # TestApp Should have test ID of the manifest
    assert issubclass(TestApp, BaseTestApp)
    assert TestApp.test_id == "manifest"

    # Confirm extends works as per
    # tests/test_base_def.py:test_apply_base_manifest__extends__merges_base_classes

    # Should have first as the first base
    assert len(TestApp.__bases__) == 2
    assert TestApp.__bases__[0].test_id == "first"  # type: ignore
    assert TestApp.__bases__[1] is BaseTestApp

    # First should have second as first base
    assert len(TestApp.__bases__[0].__bases__) == 2
    assert TestApp.__bases__[0].__bases__[0].test_id == "second"  # type: ignore
    assert TestApp.__bases__[0].__bases__[1] is BaseApp

    # And inheritance order should give these values
    assert TestApp.compose == "first"
    assert TestApp.env_file == "second"

    # OtherApp should exist
    assert issubclass(OtherApp, App)
    assert OtherApp.path == "other_app"

    # Host
    assert issubclass(VagrantHost, Host)
    assert VagrantHost.name == "localhost"
    assert VagrantHost.port == 2222
    assert VagrantHost.user == "vagrant"
