"""
Test constants
"""

#
# Live integration URLs
#

# This file exists in the repo
GITHUB_EXISTS = "git+https://github.com/radiac/docker0s@main#tests/data/file.txt"
GITHUB_EXISTS_PARTS = (
    "https://github.com/radiac/docker0s",
    "main",
    "tests/data/file.txt",
)
GITHUB_EXISTS_CONTENT = "All work and no play makes docker0s happy"

# This file does not exist in the repo
GITHUB_MISSING = "git+https://github.com/radiac/docker0s@main#tests/data/does.not.exist"
GITHUB_MISSING_PARTS = (
    "https://github.com/radiac/docker0s",
    "main",
    "tests/data/does.not.exist",
)

# Private clone of docker0s repo for testing authentication
# Also uses ssh
GITHUB_PRIVATE = (
    "git+ssh://git@github.com:radiac/docker0s-private@main#tests/data/file.txt"
)
GITHUB_PRIVATE_PARTS = (
    "git@github.com:radiac/docker0s-private",
    "main",
    "tests/data/file.txt",
)
GITHUB_PRIVATE_CONTENT = GITHUB_EXISTS_CONTENT

# Fixture constants
HOST_NAME = "localhost"
