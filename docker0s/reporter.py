from __future__ import annotations

import sys
from functools import cached_property
from threading import Thread
from typing import TYPE_CHECKING

from click import Abort
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt


if TYPE_CHECKING:
    from rich.console import RenderableType


class ReporterError(Abort):
    pass


class ProgressTask:
    reporter: Reporter

    def __init__(self, reporter, task_id):
        self.reporter = reporter
        self.task_id = task_id

    def __enter__(self):
        self.reporter.progress.start_task(self.task_id)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reporter.progress.stop_task(self.task_id)
        self.reporter.progress.remove_task(self.task_id)
        self.reporter.progress.refresh()

    def update(self, description):
        self.reporter.progress.update(self.task_id, description=description)


class Reporter:
    """
    Report status and log messages

    Convenience wrapper around rich
    """

    console: Console
    progress: Progress

    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TimeElapsedColumn(),
            TextColumn("{task.description}"),
            console=self.console,
            transient=True,
            redirect_stdout=True,
            redirect_stderr=True,
        )
        self.progress.start()

    @cached_property
    def can_debug(self):
        from .config import settings

        return settings.DEBUG

    def print(self, msg: RenderableType):
        """
        Print a message to screen

        This is the intentional output of a command.
        """
        self.console.print(msg)

    def info(self, msg: RenderableType):
        """
        Display an informational note. This will usually be shown to the user.
        """
        self.console.print(msg)

    def debug(self, msg: RenderableType):
        """
        Display a debug note. This will usually not be shown to the user.

        Note: settings.DEBUG is detected the first time debug() is called. If the
        settings change after that, you'll need to ``del reporter.can_debug`` before
        calling this again.
        """
        if self.can_debug:
            self.console.print(msg)

    def warn(self, msg: RenderableType):
        self.console.print(msg, style="yellow bold")

    def error(self, msg: RenderableType) -> ReporterError:
        """
        Report an error

        The message is displayed using rich, and it returns a ReporterError - a
        click.Abort subclass which can be raised to terminate docker0s without
        displaying the exception message again.

        Usage::

            reporter.error("Something went wrong but I am continuing to run")
            raise reporter.error("Something went wrong and I give up")
        """
        self.console.print(msg, style="red bold")
        return ReporterError(msg)

    def print_exception(self):
        if self.can_debug:
            self.console.print_exception(show_locals=True)
        else:
            self.print("Traceback suppressed, run with --debug to see")

    def task(self, description: str, total=None) -> ProgressTask:
        """
        Add a task to the progress indicator.

        Does not auto-start.

        Returns a ProgressTask

        Usage::

            with reporter.task(message) as task:
                task.update("Updated")
        """
        task_id = self.progress.add_task(description, total=total, start=False)

        return ProgressTask(self, task_id)

    def prompt(self, prompt, *, password=False) -> str:
        """
        Prompt the user for input
        """
        response = Prompt.ask(prompt, console=self.console, password=password)
        return response

    def panel(self, msg: RenderableType):
        """
        Print content in a panel
        """
        self.print(Panel(msg))


reporter = Reporter()


class ReportingThread(Thread):
    """
    A thread which logs and reports exceptions

    Usage::

        thread.join()
        if thread.exception:
            raise reporter.error("Thread failed")
    """

    exception: Exception | None

    def __init__(self, *args, terminating=False, **kwargs):
        """
        Args:

            terminating (bool): If an exception occurs, terminate the program
        """
        super().__init__(*args, **kwargs)
        self.terminating = terminating
        self.exception = None

    def run(self, *args, **kwargs):
        try:
            super().run(*args, **kwargs)
        except Exception as e:
            self.exception = e
            reporter.error(f"Thread experienced an exception: {e}")
            reporter.print_exception()
            if self.terminating:
                sys.exit(1)
