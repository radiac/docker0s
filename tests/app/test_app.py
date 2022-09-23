"""
Test docker0s.app.app.App
"""
from docker0s.app.app import App


def test_app_is_abstract():
    assert App.abstract is True


def test_app_subclass_is_concrete():
    class TestApp(App):
        pass

    assert TestApp.abstract is False
