from pathlib import Path

import pytest

from docker0s.git import fetch_repo
from docker0s.path import ManifestPath

from ..constants import GITHUB_EXISTS, GITHUB_EXISTS_CONTENT, GITHUB_MISSING


manifest_dir = Path("/foo/bar")
relative_paths = [
    (
        ManifestPath("traefik.yml", manifest_dir=manifest_dir),
        "/foo/bar/traefik.yml",
    ),
    (
        ManifestPath("app/traefik.yml", manifest_dir=manifest_dir),
        "/foo/bar/app/traefik.yml",
    ),
    (
        ManifestPath("../traefik.yml", manifest_dir=manifest_dir),
        "/foo/traefik.yml",
    ),
]

absolute_paths = [
    (
        ManifestPath("/traefik.yml", manifest_dir=manifest_dir),
        "/traefik.yml",
    ),
    (
        ManifestPath("/app/traefik.yml", manifest_dir=manifest_dir),
        "/app/traefik.yml",
    ),
]

git_parts = [
    (
        ManifestPath(
            "git+ssh://git@github.com:radiac/docker0s@main#apps/traefik/manifest.yml",
            manifest_dir=manifest_dir,
        ),
        {
            "url": "git@github.com:radiac/docker0s",
            "ref": "main",
            "path": "apps/traefik/manifest.yml",
        },
    ),
    (
        ManifestPath(
            "git+https://github.com/radiac/docker0s@main#apps/traefik/manifest.yml",
            manifest_dir=manifest_dir,
        ),
        {
            "url": "https://github.com/radiac/docker0s",
            "ref": "main",
            "path": "apps/traefik/manifest.yml",
        },
    ),
    (
        ManifestPath(
            "git+https://github.com/radiac/docker0s@main",
            manifest_dir=manifest_dir,
        ),
        {
            "url": "https://github.com/radiac/docker0s",
            "ref": "main",
            "path": "",
        },
    ),
    (
        ManifestPath(
            "git+https://github.com/radiac/docker0s#apps/traefik/manifest.yml",
            manifest_dir=manifest_dir,
        ),
        {
            "url": "https://github.com/radiac/docker0s",
            "ref": "",
            "path": "apps/traefik/manifest.yml",
        },
    ),
    (
        ManifestPath(
            "git+https://github.com/radiac/docker0s",
            manifest_dir=manifest_dir,
        ),
        {
            "url": "https://github.com/radiac/docker0s",
            "ref": "",
            "path": "",
        },
    ),
]

local_paths = relative_paths + absolute_paths


@pytest.mark.parametrize("path, absolute", local_paths)
class TestLocal:
    """
    Test local paths
    """

    def test_local__is_local__true(self, path, absolute):
        assert path.is_local is True

    def test_local__is_git__false(self, path, absolute):
        assert path.is_git is False

    def test_local__absolute__matches(self, path, absolute):
        assert path.absolute == Path(absolute)

    def test_local__parts__raises_valueerror(self, path, absolute):
        with pytest.raises(
            ValueError, match="ManifestPath.parts only supports git URLs"
        ):
            _ = path.parts

    def test_local__get_local_path(self, path, absolute):
        assert path.get_local_path() == Path(absolute)


@pytest.mark.parametrize("path, absolute", relative_paths)
def test_relative__is_absolute__false(path, absolute):
    assert path.is_absolute is False


@pytest.mark.parametrize("path, absolute", absolute_paths)
def test_absolute__is_absolute__false(path, absolute):
    assert path.is_absolute is True


@pytest.mark.parametrize(
    "path_str, uuid",
    [
        # Manifest dir is /foo/bar
        ("foo.py", "_a2f4503a3f1da6f32c0ae0d5f182aeec"),
        ("/foo.py", "_7a32759789e8efe7c60b4448755c2a9f"),
        (
            "git+https://github.com/radiac/docker0s#foo.yml",
            "_279ca20400721f4ab22e5c56a7699207",
        ),
    ],
)
def test_uuid(path_str, uuid):
    path = ManifestPath(path_str, manifest_dir=manifest_dir)
    assert path.uuid == uuid


@pytest.mark.parametrize(
    "path_str, filetype",
    [
        ("foo.py", ".py"),
        ("FOO.PY", ".py"),
        ("foo.yml", ".yml"),
        ("FOO.YAML", ".yml"),
        (
            "git+ssh://git@github.com:radiac/docker0s@main#apps/traefik/manifest.yml",
            ".yml",
        ),
        ("foo/bar", ""),
    ],
)
def test_suffix(path_str, filetype):
    path = ManifestPath(path_str, manifest_dir=manifest_dir)
    assert path.filetype == filetype


def test_local__exists_file_exists__true(tmp_path):
    file_path = tmp_path / "test"
    file_path.write_text("data")
    path = ManifestPath("test", manifest_dir=tmp_path)
    assert path.exists() is True


def test_local__exists_file_missing__false(tmp_path):
    path = ManifestPath("test", manifest_dir=tmp_path)
    assert path.exists() is False


def test_local__read_text__returns_text(tmp_path):
    file_path = tmp_path / "test"
    file_path.write_text("data")
    path = ManifestPath("test", manifest_dir=tmp_path)
    assert path.read_text() == "data"


@pytest.mark.parametrize("path, parts", git_parts)
class TestGit:
    """
    Test git paths
    """

    def test_git__is_local__false(self, path, parts):
        assert path.is_local is False

    def test_git__is_git__true(self, path, parts):
        assert path.is_git is True

    def test_git__absolute__raises_valueerror(self, path, parts):
        with pytest.raises(
            ValueError, match="ManifestPath.absolute only supports local URLs"
        ):
            _ = path.absolute

    def test_git__parts__returns_parts(self, path, parts):
        assert path.parts == parts


def test_git__exists_file_missing__false(tmp_path, mock_call):
    # This file does not exist
    fetch_repo.cache_clear()
    path = ManifestPath(GITHUB_MISSING, manifest_dir=tmp_path)
    with mock_call():
        result = path.exists()
    assert result is False


def test_git__exists_file_exists__true(tmp_path, mock_call, mock_file):
    # This file does exist
    fetch_repo.cache_clear()
    file = GITHUB_EXISTS
    path = ManifestPath(file, manifest_dir=tmp_path)

    with mock_call():
        result = path.exists()
    assert result is True


def test_git__local_path_file_exists__path(tmp_path, mock_call, mock_file):
    # This file does exist
    fetch_repo.cache_clear()
    file = GITHUB_EXISTS
    path = ManifestPath(file, manifest_dir=tmp_path)

    with mock_call():
        result = path.get_local_path()
    assert result == mock_file[3]


def test_git__read_text__returns_text(tmp_path, mock_call, mock_file):
    # This file does exist
    fetch_repo.cache_clear()
    file = GITHUB_EXISTS
    path = ManifestPath(file, manifest_dir=tmp_path)

    with mock_call():
        result = path.read_text()
    assert result == GITHUB_EXISTS_CONTENT
