"""
Test docker0s.app.mounted.Mounted
"""
from docker0s.app.mounted import MountedApp


def test_mountedapp_is_abstract():
    assert MountedApp.abstract is True


def test_mountedapp_subclass_is_concrete():
    class TestApp(MountedApp):
        pass

    assert TestApp.abstract is False
