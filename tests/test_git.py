import hashlib

import pytest

from docker0s.git import CommandError, call_or_die, fetch_repo

from .constants import GITHUB_EXISTS_PARTS


def test_call_or_die__success__returns_response(tmp_path):
    msg = "Hello"
    result = call_or_die("echo", msg, cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.decode() == f"{msg}\n"


def test_call_or_die__confirm_run_handles_spaces(tmp_path):
    # We know it does, just to sanity check safety
    filename = "Hello there"
    file = tmp_path / filename
    msg = "Hello"
    file.write_text(msg)

    result = call_or_die("cat", filename, cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.decode() == msg


def test_call_or_die__error__commanderror(tmp_path):
    with pytest.raises(CommandError, match="Command failed with exit code 1"):
        _ = call_or_die("cat", "missing", cwd=tmp_path)


def test_call_or_die__content_error__commanderror(tmp_path):
    filename = "test"
    file = tmp_path / filename
    file.write_text("hello")
    with pytest.raises(CommandError, match="Command failed with unexpected output"):
        _ = call_or_die("cat", filename, cwd=tmp_path, expected="bye")


def test_fetch_repo__not_in_cache__clones_and_pulls(mock_call, cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS
    repo_path = cache_path / hashlib.md5(url.encode()).hexdigest()

    with mock_call() as mocked:
        fetch_repo(url=url, ref=ref)

    assert mocked.cmd_cwd_stack == [
        (("mkdir", "-p", str(repo_path)), None),
        (("git", "init"), repo_path),
        (("git", "remote", "add", "origin", url), repo_path),
        (("git", "fetch", "origin", ref, "--depth=1"), repo_path),
        (("git", "checkout", ref), repo_path),
    ]


def test_fetch_repo__in_cache__just_pulls(mock_call, cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS
    repo_path = cache_path / hashlib.md5(url.encode()).hexdigest()

    repo_path.mkdir()
    with mock_call() as mocked:
        fetch_repo(url=url, ref=ref)

    assert mocked.cmd_cwd_stack == [
        (("git", "fetch", "origin", ref, "--depth=1"), repo_path),
        (("git", "checkout", ref), repo_path),
    ]
