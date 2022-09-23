import hashlib
import os

import pytest

from docker0s.git import (
    CommandError,
    call_or_die,
    exists,
    fetch_file,
    fetch_repo,
    read_text,
    stream_text,
)

from .constants import (
    GITHUB_EXISTS_CONTENT,
    GITHUB_EXISTS_PARTS,
    GITHUB_MISSING_PARTS,
    GITHUB_PRIVATE_CONTENT,
    GITHUB_PRIVATE_PARTS,
)


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


@pytest.mark.parametrize(
    "test_path, expected_path",
    [
        ("inside", "inside"),
        ("/absolute", "absolute"),
    ],
)
def test_fetch_file__file_inside_repo__file_fetched(
    test_path, expected_path, mock_call, cache_path
):
    fetch_repo.cache_clear()
    url, ref, _ = GITHUB_EXISTS_PARTS
    repo_path = cache_path / hashlib.md5(url.encode()).hexdigest()

    with mock_call():
        file = fetch_file(url=url, ref=ref, path=test_path)

    assert file == repo_path / expected_path


@pytest.mark.parametrize(
    "invalid_path",
    [
        "../outside",
    ],
)
def test_fetch_file__file_outside_repo__valueerror(invalid_path, mock_call, cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS
    with mock_call():
        with pytest.raises(ValueError, match=f"Invalid path {invalid_path}"):
            _ = fetch_file(url=url, ref=ref, path=invalid_path)


@pytest.mark.skipif(
    not os.getenv("TEST_INTEGRATION_PUBLIC", False),
    reason="TEST_INTEGRATION_PUBLIC not set",
)
def test_fetch_file__public_repo__file_pulled(cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS
    file = fetch_file(url=url, ref=ref, path=path)

    assert file.exists()
    assert file.read_text() == GITHUB_EXISTS_CONTENT


@pytest.mark.skipif(
    not os.getenv("TEST_INTEGRATION_PUBLIC", False),
    reason="TEST_INTEGRATION_PUBLIC not set",
)
def test_fetch_file__public_repo_missing_ref___commanderror(cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS

    with pytest.raises(CommandError) as exc_info:
        _ = fetch_file(url=url, ref="_test/does-not-exist", path=path)

    assert exc_info.type is CommandError
    exc: CommandError = exc_info.value
    assert exc.args[0] == "Command failed with exit code 128"
    assert exc.result is not None
    assert (
        exc.result.stderr.decode()
        == "fatal: couldn't find remote ref _test/does-not-exist\n"
    )


@pytest.mark.skipif(
    not os.getenv("TEST_INTEGRATION_PUBLIC", False),
    reason="TEST_INTEGRATION_PUBLIC not set",
)
def test_fetch_file__public_repo_missing_file__file_not_exist(cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_MISSING_PARTS
    file = fetch_file(url=url, ref=ref, path=path)

    assert not file.exists()


@pytest.mark.skipif(
    not os.getenv("TEST_INTEGRATION_PRIVATE", False),
    reason="TEST_INTEGRATION_PRIVATE not set",
)
def test_fetch_file__private_repo__file_pulled(cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_PRIVATE_PARTS
    file = fetch_file(url=url, ref=ref, path=path)

    assert file.exists()
    assert file.read_text() == GITHUB_PRIVATE_CONTENT


def test_exists__file_found__returns_true(mock_call, mock_file):
    fetch_repo.cache_clear()
    url, ref, path, file_path = mock_file
    with mock_call():
        result = exists(url=url, ref=ref, path=path)
    assert result is True


def test_exists__file_missing__returns_false(mock_call, cache_path):
    fetch_repo.cache_clear()
    url, ref, path = GITHUB_EXISTS_PARTS
    with mock_call():
        result = exists(url=url, ref=ref, path=path)
    assert result is False


def test_read_text__file_exists__returns_string(mock_call, mock_file):
    fetch_repo.cache_clear()
    url, ref, path, file_path = mock_file
    with mock_call():
        content = read_text(url=url, ref=ref, path=path)
    assert content == GITHUB_EXISTS_CONTENT


def test_stream_text__file_exists__returns_io(mock_call, mock_file):
    fetch_repo.cache_clear()
    url, ref, path, file_path = mock_file
    with mock_call():
        handle = stream_text(url=url, ref=ref, path=path)
    assert handle.read() == GITHUB_EXISTS_CONTENT
