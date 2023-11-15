import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Any, Self

from .config import settings
from .reporter import ReportingThread, reporter


def now() -> int:
    return int(time.time())


@dataclass
class CacheRepo:
    url: str
    timestamp: int

    @property
    def dir_name(self):
        return hashlib.md5(self.url.encode()).hexdigest()

    @property
    def path(self):
        return settings.CACHE_PATH / self.dir_name

    @property
    def age(self):
        return now() - self.timestamp

    @property
    def is_cached(self):
        if not self.timestamp:
            is_cached = False
        elif (
            settings.CACHE_ENABLED
            and settings.CACHE_AGE
            and self.age < settings.CACHE_AGE
        ):
            is_cached = True
        else:
            is_cached = False

        reporter.debug(
            f"Cache check\n"
            f"  Cache: {'enabled' if settings.CACHE_ENABLED else 'disabled'}\n"
            f"  URL: {self.url}\n"
            f"  Cache path: {self.path} {'exists' if self.path.is_dir() else 'not found'}\n"
            f"  Cache age: {self.age}\n"
            f"  Cache hit? {is_cached}"
        )
        return is_cached


class CacheState:
    #: Path to the state file
    path: Path

    #: CacheRepo data
    _repos: dict[str, CacheRepo]

    _thread: ReportingThread
    _update_queue: Queue

    def __init__(self, path: Path, repos):
        self.path = path
        self._repos = repos
        self._update_queue = Queue()
        self._thread = ReportingThread(
            target=self._handle_update, daemon=True, terminating=True
        )
        self._thread.start()

    @property
    def repos(self) -> dict[str, CacheRepo]:
        return self._repos

    @classmethod
    def from_file(cls, path: Path):
        reporter.debug(f"Checking for cache at {path}")
        repos = {}
        if path.is_file():
            with path.open("r") as file:
                data = json.load(file)
            repos = {url: CacheRepo(**state) for url, state in data.items()}
        else:
            reporter.debug(f"No cache found at {path}")
        state = cls(path, repos)
        return state

    def save(self):
        data = {url: asdict(state) for url, state in self.repos.items()}
        with self.path.open("w") as file:
            json.dump(data, file)
        reporter.debug(f"Cache saved")

    def get_or_create(
        self,
        url: str,
        timestamp: int | None = None,
    ) -> CacheRepo:
        """
        Retries a CacheRepo from the cache or creates a new one with an expired cache

        Does not save
        """
        cache = self.repos.get(url)
        if cache is None:
            cache = CacheRepo(
                url=url,
                timestamp=timestamp or 0,
            )
        return cache

    def update(self, url: str, cache: CacheRepo | None = None):
        self._update_queue.put((url, cache))

    def _handle_update(self):
        url: str
        cache: CacheRepo | None
        while True:
            (url, cache) = self._update_queue.get()
            if cache is None:
                cache = self.get_or_create(url)
            cache.timestamp = now()
            self._repos[url] = cache
            self.save()
            self._update_queue.task_done()
