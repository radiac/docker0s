"""
Test the core functionality of app definitions - the classmethods which manage how an
app collects and processes its attributes.
"""

from pathlib import Path
from unittest.mock import Mock

from docker0s.app import BaseApp


manifest_dir = Path(__file__).parent


def test_baseapp__is_abstract():
    assert BaseApp.abstract is True


def test_baseapp__subclass_is_concrete():
    class TestApp(BaseApp):
        pass

    assert TestApp.abstract is False


def test_baseapp__get_name():
    class TestApp(BaseApp):
        pass

    assert TestApp.get_name() == "TestApp"


def test_baseapp__manifest_path_detected():
    class TestApp(BaseApp):
        pass

    assert TestApp._file == Path(__file__)


def test_baseapp__manifest_dir_dectected():
    class TestApp(BaseApp):
        pass

    assert TestApp._dir == Path(__file__).parent


def test_apply_base_manifest__no_extends__no_base_loaded(monkeypatch, mock_lock):
    class TestApp(BaseApp):
        pass

    # Should return from initial ``if not cls.extends`` and shouldn't ``get_manifest``
    mock_get_manifest = Mock()
    monkeypatch.setattr("docker0s.path.ExtendsPath.get_manifest", mock_get_manifest)

    TestApp.apply_base_manifest(lock=mock_lock)
    mock_get_manifest.assert_not_called()


def test_apply_base_manifest__extends__merges_base_classes(tmp_path, mock_lock):
    """
    TestApp extends first.py::TestApp, which extends second.py::TestApp
    """

    class TestApp(BaseApp):
        extends = "../data/extends_base_first.py"

    # Apply ``extends``
    print(
        "TESTAPP_DIR",
        TestApp._file,
        TestApp._dir,
        (TestApp._dir / "../data/extends_base_first.py").resolve(),
    )
    TestApp.apply_base_manifest(lock=mock_lock)

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
