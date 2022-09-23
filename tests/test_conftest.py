"""
Test the conftest fixtures
"""
from docker0s import git


def test_mock_call__calls_logged(mock_call, tmp_path):
    dir_1 = tmp_path / "dir_1"
    dir_2 = tmp_path / "dir_2"

    with mock_call() as mocked:
        git.call_or_die("one", "foo", cwd=dir_1, expected="bar")
        git.call_or_die("two", "bar", cwd=dir_2, expected="foo")

    assert mocked.stack[0].cmd == ("one", "foo")
    assert mocked.stack[0].cwd == dir_1
    assert mocked.stack[0].expected == "bar"

    assert mocked.stack[1].cmd == ("two", "bar")
    assert mocked.stack[1].cwd == dir_2
    assert mocked.stack[1].expected == "foo"


def test_mock_call__calls_logged__cmd_cwd_stack(mock_call, tmp_path):
    dir_1 = tmp_path / "dir_1"
    dir_2 = tmp_path / "dir_2"

    with mock_call() as mocked:
        git.call_or_die("one", "foo", cwd=dir_1, expected="bar")
        git.call_or_die("two", "bar", cwd=dir_2, expected="foo")

    assert mocked.cmd_cwd_stack == [
        (("one", "foo"), dir_1),
        (("two", "bar"), dir_2),
    ]
