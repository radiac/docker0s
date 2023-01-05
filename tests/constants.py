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


# Fixture constants
HOST_NAME = "localhost"
