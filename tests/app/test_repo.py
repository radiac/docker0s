"""
Test docker0s.app.repo.RepoApp
"""
from docker0s.app.repo import RepoApp


def test_repoapp_is_abstract():
    assert RepoApp.abstract is True


def test_repoapp_subclass_is_concrete():
    class TestApp(RepoApp):
        pass

    assert TestApp.abstract is False
