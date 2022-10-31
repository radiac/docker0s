"""
Test the core functionality of app definitions - the classmethods which manage how an
app collects and processes its attributes.
"""

from pathlib import Path

from docker0s.app import BaseApp
from docker0s.path import AppPath, ManifestPath


manifest_dir = Path(__file__).parent


def test_baseapp_is_abstract():
    assert BaseApp.abstract is True


def test_baseapp_subclass_is_concrete():
    class TestApp(BaseApp):
        pass

    assert TestApp.abstract is False


def test_get_name():
    class TestApp(BaseApp):
        pass

    assert TestApp.get_name() == "TestApp"


def test_get_manifest_path():
    class TestApp(BaseApp):
        pass

    assert TestApp.get_manifest_path() == Path(__file__)


def test_get_manifest_dir():
    class TestApp(BaseApp):
        pass

    assert TestApp.get_manifest_dir() == manifest_dir


def test_get_path(tmp_path):
    class TestApp(BaseApp):
        path = str(tmp_path)

    actual = TestApp.get_path()
    expected = ManifestPath(str(tmp_path), manifest_dir=manifest_dir)
    assert actual.original == expected.original
    assert actual.manifest_dir == manifest_dir


def test_mk_app_path(tmp_path):
    class TestApp(BaseApp):
        path = str(tmp_path)

    actual = TestApp._mk_app_path("app://foo")
    expected = AppPath("app://foo", manifest_dir=manifest_dir, app=TestApp)

    assert actual.original == expected.original
    assert actual.manifest_dir == manifest_dir


def test_get_base_manifest__no_extends__returns_none(tmp_path):
    class TestApp(BaseApp):
        path = str(tmp_path)

    assert TestApp._get_base_manifest() is None


def test_get_base_manifest__extends__returns_app_path(tmp_path):
    class TestApp(BaseApp):
        path = str(tmp_path)
        extends = "../data/extends_base_first.py"

    path = TestApp._get_base_manifest()
    expected = (manifest_dir / ".." / "data" / "extends_base_first.py").resolve()

    assert isinstance(path, AppPath)
    assert path.absolute == expected


def test_apply_base_manifest__extends__merges_base_classes(tmp_path):
    """
    TestApp extends first.py::TestApp, which extends second.py::TestApp
    """

    class TestApp(BaseApp):
        path = str(tmp_path)
        extends = "../data/extends_base_first.py"

    # Apply ``extends``
    TestApp.apply_base_manifest()

    # Should have first as the first base
    assert len(TestApp.__bases__) == 2
    assert TestApp.__bases__[0].test_id == "first"  # type: ignore
    assert TestApp.__bases__[1] is BaseApp

    # First should have second as first base
    assert len(TestApp.__bases__[0].__bases__) == 2
    assert TestApp.__bases__[0].__bases__[0].test_id == "second"  # type: ignore
    assert TestApp.__bases__[0].__bases__[1] is BaseApp

    # And inheritance order should give these values
    assert TestApp.compose == "first"
    assert TestApp.env_file == "second"


def test_env__dict_only__returned():
    env_data: dict[str, str | int] = {
        "key1": "value1",
        "key2": "value2",
    }

    class TestApp(BaseApp):
        env = env_data
        set_project_name = False

    assert TestApp.get_env_data() == env_data


def test_env__file_only__loaded():
    class TestApp(BaseApp):
        env_file = "../data/first.env"
        set_project_name = False

    assert TestApp.get_env_data() == {
        "key1": "first1",
        "key2": "first2",
        "key3": "first3",
    }


def test_env__two_files__merged_in_order():
    class TestApp(BaseApp):
        env_file = ["../data/first.env", "../data/second.env"]
        set_project_name = False

    assert TestApp.get_env_data() == {
        "key1": "second1",
        "key2": "first2",
        "key3": "first3",
        "key4": "second4",
    }


def test_env__two_files_and_dict__merged_in_order():
    class TestApp(BaseApp):
        env_file = ["../data/first.env", "../data/second.env"]
        env = {
            "key3": "data3",
            "key5": "data5",
        }
        set_project_name = False

    assert TestApp.get_env_data() == {
        "key1": "second1",
        "key2": "first2",
        "key3": "data3",
        "key4": "second4",
        "key5": "data5",
    }


def test_env__data_and_set_project_name__merged_in_order_with_project_name():
    class TestApp(BaseApp):
        env_file = ["../data/first.env", "../data/second.env"]
        env = {
            "key3": "data3",
            "key5": "data5",
        }

    assert TestApp.get_env_data() == {
        "COMPOSE_PROJECT_NAME": "test_app",
        "key1": "second1",
        "key2": "first2",
        "key3": "data3",
        "key4": "second4",
        "key5": "data5",
    }


def test_env__two_files_and_two_dicts_inherited_and_set_project_name__merged_in_order():
    class ParentApp(BaseApp):
        env_file = "../data/first.env"
        env = {
            "key1": "parent1",
            "key3": "parent3",
            "key5": "parent5",
        }

    class ChildApp(ParentApp):
        env_file = "../data/second.env"
        env = {"key3": "child3"}

    # Value first comes from parent file, second comes from child file
    # Child env_file overrides parent env
    assert ChildApp.get_env_data() == {
        "COMPOSE_PROJECT_NAME": "child_app",
        "key1": "second1",
        "key2": "first2",
        "key3": "child3",
        "key4": "second4",
        "key5": "parent5",
    }
