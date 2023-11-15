"""
Each manifest has a lock file for any upstream resources

Each lock hash must cover at least:

* d0s-manifest.yml or d0s-manifest.py
* d0s-manifest.lock
* docker-compose.yml
"""
import json
from typing import TYPE_CHECKING, Self

from .exceptions import DefinitionError, LockError
from .reporter import reporter


if TYPE_CHECKING:
    from pathlib import Path

    from .app.base import BaseApp
    from .manifest import Manifest


# Current lockfile file format version
CURRENT_VERSION = 1


class AppLock:
    name: str
    origin: str
    hash: str
    date: str

    def __init__(self, name: str, origin: str, hash: str, date: str):
        self.name = name
        self.origin = origin
        self.hash = hash
        self.date = date

    def to_json(self) -> dict[str, str]:
        return {
            "origin": self.origin,
            "hash": self.hash,
            "date": self.date,
        }

    def assert_ok(self, repo: str, ref: str | None) -> bool:
        if not repo:
            raise LockError("Cannot apply a lock to an origin missing the repository")
        if repo != self.origin:
            raise LockError("Origin git url has changed since locking")
        if ref and ref != self.hash:
            raise LockError("Lock and origin reference hashes do not match")
        return True


# TODO:
# lockfile needs to store information about the bases this manifest inherits from
# so we need to store:
#   origin. If user changed it, the lockfile is invalid even if the hash matches
#   hash. Commit hash of the remote when it was last locked
#
# We dont need to worry about whether someone messed with the lockfile, we trust here
#
# lockfile should be loaded before the manifest
# lockfile should have references to app name
# manifest loader looks in lockfile for app name references
# manifest loader adds lock hash to app before loading remote
# lock hash overrides any extends hash - that way we can manage an upgrade
# if manifest specifies git commit, error if it doesntmatch hash
class Lockfile:
    """
    Lockfile

    Format:

        {
            "version": 1,
            "apps": {
                "app_name": {
                    "origin": "extends",
                    "hash": "hash",
                    "date": "YYYY-MM-DDThh:mm:ssZ",
                }
            }
        }
    """

    path: Path
    apps: dict[str, AppLock]

    def __init__(self, path: Path, apps: dict[str, dict[str, str]]):
        self.path = path
        self.apps = {
            app_name: AppLock(name=app_name, **app_data)
            for app_name, app_data in apps.items()
        }

    def get_app_lock(self, name: str) -> Lock:
        if name not in self.apps:
            self.apps[name] = AppLock(name=name)
        return self.apps[name]

    @classmethod
    def load(cls, path: Path) -> Self:
        if not path.exists():
            reporter.debug(f"No lockfile at {path}")
            return cls(path, {})

        with path.open("r") as file:
            raw_data = json.load(file)

        if raw_data.get("version") == CURRENT_VERSION:
            raise DefinitionError("Invalid lockfile version")

        if "apps" not in raw_data:
            raise DefinitionError("Invalid lockfile format, apps section missing")

        apps = raw_data["apps"]
        lockfile = cls(path, apps)
        return lockfile

    def save(self):
        data = {
            "version": CURRENT_VERSION,
            "apps": {app.name: app.to_json() for app in self.apps.values()},
        }
        return data
