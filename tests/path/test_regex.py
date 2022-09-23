from docker0s.path import GIT_HTTPS_PATTERN, GIT_SSH_PATTERN


ssh_url = "git+ssh://git@github.com:username/repo@branch#path/to/file"
https_url = "git+https://github.com/username/repo@branch#path/to/file"


def test_git_ssh_pattern__ssh_pattern__match():
    matches = GIT_SSH_PATTERN.match(ssh_url)
    assert matches
    data = matches.groupdict()
    assert data == {
        "url": "git@github.com:username/repo",
        "ref": "branch",
        "path": "path/to/file",
    }


def test_git_ssh_pattern__not_ssh_pattern__no_match():
    matches = GIT_SSH_PATTERN.match(https_url)
    assert not matches


def test_git_https_pattern__https_pattern__match():
    matches = GIT_HTTPS_PATTERN.match(https_url)
    assert matches
    data = matches.groupdict()
    assert data == {
        "url": "https://github.com/username/repo",
        "ref": "branch",
        "path": "path/to/file",
    }


def test_git_https_pattern__not_https_pattern__no_match():
    matches = GIT_HTTPS_PATTERN.match(ssh_url)
    assert not matches
