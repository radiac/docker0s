from pathlib import Path

import pytest

from docker0s.exceptions import DefinitionError
from docker0s.path import path_to_relative, path_to_uuid


@pytest.mark.parametrize(
    "path_str, uuid",
    [
        ("/foo.py", "_7a32759789e8efe7c60b4448755c2a9f"),
        (
            "git+https://github.com/radiac/docker0s#foo.yml",
            "_773f52a79994eda777ad5db5be3960d8",
        ),
    ],
)
def test_uuid(path_str, uuid):
    actual_uuid = path_to_uuid(Path(path_str))
    assert actual_uuid == uuid


@pytest.mark.parametrize(
    "root, path, expected",
    [
        ("/foo", "/foo/bar", "bar"),
        ("/foo", "/foo/bar/../baz", "bar/../baz"),
    ],
)
def test_path_to_relative__relative_path__resolves(root, path, expected):
    actual = path_to_relative(Path(root), Path(path))
    assert actual == expected


@pytest.mark.parametrize(
    "root, path",
    [
        ("/foo/bar", "../baz"),
        ("/foo/bar", "baz/../../qux"),
        ("/foo/bar", "/baz/qux"),
    ],
)
def test_path_to_relative__invalid_path__raises_exception(root, path):
    with pytest.raises(
        DefinitionError, match=f"Path {path} is not a sub-path of {root}"
    ):
        path_to_relative(Path(root), Path(path))
