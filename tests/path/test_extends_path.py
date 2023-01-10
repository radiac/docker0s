from pathlib import Path

import pytest

from docker0s.exceptions import DefinitionError
from docker0s.path import ExtendsPath


@pytest.fixture
def mock_fetch_repo(monkeypatch, tmp_path):
    """
    Mock path.fetch_repo

    Usage::

        def test_call(mock_fetch_repo):
            with mock_fetch_repo(stdout="stdout response") as mocked:
                trigger_fetch_repo('ls')
            assert mocked.stack[0].cmd = ['ls']
    """

    class MockedCall:
        def __enter__(self):
            monkeypatch.setattr("docker0s.path.fetch_repo", self)
            self.stack = []
            return self

        def __exit__(self, *args):
            pass

        def __call__(self, url: str, ref: str) -> Path:
            path = tmp_path / "repo"
            path.mkdir()
            self.stack.append((url, ref))
            return path

    return MockedCall


@pytest.fixture()
def assert_no_fetch_repo(mock_fetch_repo):
    """
    Assert the test makes no system call
    """
    with mock_fetch_repo() as mocked:
        yield
    assert mocked.stack == []


def test_local__constructor__no_calls(assert_no_fetch_repo, tmp_path):
    ExtendsPath("/foo/bar", cwd=tmp_path)


@pytest.mark.parametrize(
    "path_str, expected",
    [
        # Relative paths
        (
            "foo/bar/baz.yml",
            "{tmp}/foo/bar/baz.yml",
        ),
        (
            "foo/../bar.yml",
            "{tmp}/bar.yml",
        ),
        # Absolute
        (
            "{tmp}/foo.yml",
            "{tmp}/foo.yml",
        ),
        (
            "{tmp}/foo/bar.yml",
            "{tmp}/foo/bar.yml",
        ),
    ],
)
def test_local__is_resolved(
    path_str, expected, monkeypatch, tmp_path, assert_no_fetch_repo
):
    # Add tmp_path to strings
    path_str = path_str.replace("{tmp}", str(tmp_path))
    expected = expected.replace("{tmp}", str(tmp_path))

    path = ExtendsPath(path_str, cwd=tmp_path)
    assert isinstance(path.original, str)
    assert isinstance(path.path, Path)
    assert path.original == path_str
    assert str(path.path) == expected
    assert path.name is None


def test_local__path_with_name__name_extracted(monkeypatch, tmp_path):
    path_str = "app/foo.yml::bar"
    path = ExtendsPath(path_str, cwd=tmp_path)
    assert path.original == path_str
    assert path.path == tmp_path / "app/foo.yml"
    assert path.name == "bar"


def test_local__truediv__resolves_slash(assert_no_fetch_repo, tmp_path):
    path = ExtendsPath("/foo/bar", cwd=tmp_path)
    assert path / "baz" == Path("/foo/bar/baz")
    assert path / "../baz" == Path("/foo/baz")
    assert path / "/baz" == Path("/baz")


def test_local__get_manifest_file__returns_path(tmp_path, assert_no_fetch_repo):
    file_path = tmp_path / "manifest.yml"
    file_path.touch()
    path = ExtendsPath(str(file_path), cwd=tmp_path)
    assert path.get_manifest() == file_path


def test_local__get_manifest_missing__raises_exception(tmp_path, assert_no_fetch_repo):
    dir_path = tmp_path / "missing"
    with pytest.raises(DefinitionError, match=f"Manifest not found at {dir_path}"):
        path = ExtendsPath(str(dir_path), cwd=tmp_path)
        path.get_manifest()


def test_local__get_manifest_find_in_dir__finds_file(tmp_path, assert_no_fetch_repo):
    file_path = tmp_path / "manifest.yml"
    file_path.touch()
    path = ExtendsPath(str(file_path), cwd=tmp_path)
    assert path.get_manifest() == file_path


def test_local__get_manifest_missing_in_dir__raises_exception(
    tmp_path, assert_no_fetch_repo
):
    dir_path = tmp_path / "missing"
    dir_path.mkdir()
    with pytest.raises(DefinitionError, match=f"Manifest not found in {dir_path}"):
        path = ExtendsPath(str(dir_path), cwd=tmp_path)
        path.get_manifest()


@pytest.mark.parametrize(
    "path_str, data",
    [
        (
            "git+ssh://git@github.com:radiac/docker0s@main#apps/foo/manifest.yml",
            {
                "repo": "git@github.com:radiac/docker0s",
                "ref": "main",
                "path": "apps/foo/manifest.yml",
                "name": None,
            },
        ),
        (
            "git+https://github.com/radiac/docker0s@main#apps/foo/manifest.yml::bar",
            {
                "repo": "https://github.com/radiac/docker0s",
                "ref": "main",
                "path": "apps/foo/manifest.yml",
                "name": "bar",
            },
        ),
        (
            "git+https://github.com/radiac/docker0s@main",
            {
                "repo": "https://github.com/radiac/docker0s",
                "ref": "main",
                "path": "",
                "name": None,
            },
        ),
        (
            "git+https://github.com/radiac/docker0s#apps/foo/manifest.yml",
            {
                "repo": "https://github.com/radiac/docker0s",
                "ref": None,
                "path": "apps/foo/manifest.yml",
                "name": None,
            },
        ),
        (
            "git+https://github.com/radiac/docker0s::bar",
            {
                "repo": "https://github.com/radiac/docker0s",
                "ref": None,
                "path": "",
                "name": "bar",
            },
        ),
    ],
)
def test_git__constructor__calls_clone(path_str, data, tmp_path, mock_fetch_repo):
    with mock_fetch_repo() as mocked:
        path = ExtendsPath(path_str, tmp_path)
    assert path.original == path_str
    assert path.path == tmp_path / "repo" / data["path"]
    assert path.repo == data["repo"]
    assert path.ref == (data["ref"] or None)
    assert path.name == (data["name"] or None)
    assert mocked.stack == [(data["repo"], data["ref"])]


""" def xx_test_call(mock_call):
    with mock_call(stdout="stdout response") as mocked:
        call_or_die('ls')
    assert mocked.stack[0].cmd = ['ls'] """
