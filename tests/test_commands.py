from pathlib import Path

import pytest

from docker0s.commands import Target, TargetManager
from docker0s.manifest import Manifest
from docker0s.path import ManifestPath


@pytest.fixture
def manifest():
    path = ManifestPath("manifest.py", manifest_dir=Path(__file__) / "../data")
    manifest = Manifest.load(path)
    return manifest


def test_target_manager__no_targets__all_services_found(manifest):
    tm = TargetManager(manifest, ())
    # Definition order
    assert list(tm.app_lookup.keys()) == ["TestApp", "OtherApp"]
    assert tm.apps[0].get_name() == "TestApp"
    assert tm.apps[1].get_name() == "OtherApp"
    assert tm.service_lookup == {}


@pytest.mark.parametrize(
    "targets, app_names, service_lookup",
    (
        ((), ["TestApp", "OtherApp"], {}),
        ((Target("TestApp"),), ["TestApp"], {"TestApp": []}),
        (
            (
                Target("TestApp", "one"),
                Target("TestApp", "two"),
                Target("OtherApp", "three"),
            ),
            ["TestApp", "OtherApp"],
            {
                "TestApp": ["one", "two"],
                "OtherApp": ["three"],
            },
        ),
    ),
)
def test_target_manager__caches_populated(targets, app_names, service_lookup, manifest):
    tm = TargetManager(manifest, targets)
    # Definition order
    assert sorted(list(tm.app_lookup.keys())) == sorted(app_names)

    # Remap service lookup to use names, easier to parameterize tests for
    tm_service_lookup = {
        app.get_name(): services for app, services in tm.service_lookup.items()
    }
    assert sorted(tm_service_lookup) == sorted(service_lookup)


@pytest.mark.parametrize(
    "targets, app_services",
    (
        ((), [("TestApp", []), ("OtherApp", [])]),
        ((Target("TestApp"),), [("TestApp", [])]),
        (
            (
                Target("TestApp", "one"),
                Target("TestApp", "two"),
                Target("OtherApp", "three"),
            ),
            [
                ("TestApp", ["one", "two"]),
                ("OtherApp", ["three"]),
            ],
        ),
    ),
)
def test_target_manager__get_app_services(targets, app_services, manifest):
    tm = TargetManager(manifest, targets)
    tm_app_services = [
        (app.get_name(), services) for app, services in tm.get_app_services()
    ]
    assert sorted(tm_app_services) == sorted(app_services)
