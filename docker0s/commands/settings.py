import click
from rich.table import Table

from ..config import settings
from ..exceptions import UsageError
from ..reporter import reporter
from .core import cli, humanise_filesize, humanise_timestamp


@cli.command("set")
@click.argument("name", required=False)
@click.argument("value", required=False)
@click.pass_context
def cmd_set(ctx, name: str | None = None, value: str | None = None):
    if name is None:
        show_set()

    else:
        name = name.upper()
        if name not in dir(settings):
            raise UsageError(f"Setting {name} not recognised")

        settings.store(name, value)
        if value:
            reporter.print(f"Setting {name} set to {settings._store[name]}")
        else:
            reporter.print(f"Setting {name} cleared")


def show_set():
    table = Table("Setting", "Option", "Value", show_header=True)

    for name in dir(settings):
        if not name.isupper():
            continue
        table.add_row(
            name,
            f"--{name.lower().replace('_', '-')}",
            str(settings._store.get(name, f"[grey50 italic]{getattr(settings, name)}")),
        )

    reporter.print(table)
