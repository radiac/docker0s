from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from functools import wraps
from typing import Self


class PoolSession:
    """
    Context manager to wait for a collection of submitted tasks to complete
    """

    def __init__(self, pool):
        self.pool = pool
        self.futures = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        wait(self.futures)

    def submit(self, fn, *args, **kwargs):
        future = self.pool.submit(fn, *args, **kwargs)
        self.futures.append(future)
        return future


class Pool:
    """
    A decorator-based thread worker pool
    """

    _executor = None

    @property
    def executor(self) -> ThreadPoolExecutor:
        if not self._executor:
            self._executor = ThreadPoolExecutor()
        return self._executor

    def session(self) -> PoolSession:
        """
        Create a pool session to wait for a group of tasks

        Usage::

            with pool.session() as session:
                session.submit(...)
        """
        return PoolSession(self)

    def close(self):
        if self._executor:
            self._executor.shutdown()
        self._executor = None

    def __call__(self, fn):
        """
        Decorator which creates a worker pool for the lifespan of a function.

        Usage::

            @pool
            def fn(..):
                pool.submit(..)
        """
        if self._executor:
            raise ValueError("Tried to activate a pool while already active")

        @wraps(fn)
        def wrapper(*args, **kwargs):
            with self.executor:
                result = fn(*args, **kwargs)
            self.close()
            return result

        return wrapper

    def submit(self, fn, *args, **kwargs):
        """
        Submit a function and its arguments to the pool
        """
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self):
        self.executor.shutdown()
        self.close()


pool = Pool()
