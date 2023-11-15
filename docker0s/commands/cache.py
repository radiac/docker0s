import shutil
from pathlib import Path

import click
from rich.table import Table

from ..config import settings
from ..reporter import reporter
from .core import cli, humanise_filesize, humanise_timestamp


@cli.group()
@click.pass_context
def cache(ctx):
    pass


def get_dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())


@cache.command("show")
def cache_show():
    """
    Show summary of the cache
    """
    cache_state = settings.get_cache_state()

    # Summary table
    table = Table(show_header=False)
    table.add_column("Title", style="table.header", no_wrap=True)
    table.add_row(
        "Caching", "[green]enabled" if settings.CACHE_ENABLED else "[red]disabled"
    )
    if settings.CACHE_PATH.is_dir():
        table.add_row("Cache path", f"{settings.CACHE_PATH}")
        space_used = get_dir_size(settings.CACHE_PATH)
        table.add_row("Disk used", humanise_filesize(space_used))

    else:
        table.add_row("Cache path", f"{settings.CACHE_PATH} [red](does not exist)")
    table.add_row("Max age", humanise_timestamp(settings.CACHE_AGE))
    reporter.print(table)


@cache.command("flush")
def cache_flush():
    """
    Flush the cache for all manifests
    """
    if not settings.CACHE_PATH.is_dir():
        reporter.print("Cache is already empty")
        return

    with reporter.task("Removing cache"):
        shutil.rmtree(settings.CACHE_PATH)
    reporter.print("[green]Cache cleared")
