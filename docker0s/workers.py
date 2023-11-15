from __future__ import annotations

from typing import Self

from .config import settings
from .reporter import ReportingThread, reporter


# TODO: Refactor inheritance to use a thread pool
#
# Currently inheritance is recursive - when a manifest's app sees it needs to inherit
# from another, the app itself decides to get and parse the next manifest. This means we
# can't use a thread pool, as it could get exhausted. Theoretically we could end up
# with an unwieldy number of threads. It would therefore be better to use a thread pool.
#
# This will mean refactoring the inheritance code to have three stages - parse, inherit
# and apply - so that each can be sent to the thread pool independently and we can
# manage inheritance using a queue instead of recursing.
#
# Look at this at the same time as the inheritance changes in BaseApp.collect_attr


class Workers:
    """
    Context manager to run threads for a collection of submitted tasks and wait for them
    to complete
    """

    threads: list[ReportingThread]

    def __init__(self):
        self.threads = []
        # Ensure the cache is initialised before we start threads
        settings.get_cache_state()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for thread in self.threads:
            thread.join()
        if any(thread.exception for thread in self.threads):
            raise reporter.error("Workers failed")

    def submit(self, fn, *args, **kwargs):
        thread = ReportingThread(target=fn, args=args, kwargs=kwargs)
        self.threads.append(thread)
        thread.start()
