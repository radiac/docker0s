from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from click import Abort
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.status import Status


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


class ProgressHider:
    reporter: Reporter

    def __init__(self, reporter):
        self.reporter = reporter

    def __enter__(self):
        self.reporter.progress.stop()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reporter.progress.start()

    def __call__(self, fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            with self:
                result = fn(*args, **kwargs)
            return result

        return decorator


class Reporter:
    """
    Report status and log messages

    Convenience wrapper around rich
    """

    console: Console
    progress: Progress
    can_debug: bool = False

    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TimeElapsedColumn(),
            TextColumn("{task.description}"),
            console=self.console,
            transient=True,
        )
        self.progress.start()

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

    def interactive(self) -> ProgressHider:
        """
        Context manager and decorator to enter interactive mode - temporarily disable
        the progress display

        Usage::

            with reporter.interactive():
                ...

            @reporter.interactive()
            def something():
                ...
        """
        return ProgressHider(self)

    def prompt(self, prompt, *, password=False) -> str:
        """
        Prompt the user for input
        """
        with self.interactive():
            response = Prompt.ask(prompt, console=self.console, password=password)
        return response

    def panel(self, msg: RenderableType):
        """
        Print content in a panel
        """
        self.print(Panel(msg))


reporter = Reporter()
