from pathlib import Path

import click

from ..config import settings
from ..exceptions import UsageError
from ..manifest import Manifest
from ..reporter import reporter
from .core import cli


@cli.command()
@click.argument("manifest", type=str, required=False)
@click.option("--alias", "-a", type=str)
@click.option("--list", "-l", "list_alias", is_flag=True, default=False)
@click.pass_context
def use(ctx, manifest: str = "", alias: str = "", list_alias: bool = False):
    """
    Set a manifest as the default
    """
    if list_alias:
        if not settings.manifest_alias:
            reporter.print("No aliases defined")
        else:
            reporter.print("Available aliases:")
            for alias, path in sorted(settings.manifest_alias.items()):
                reporter.print(f"  {alias}: {path}")
        return

    manifest_path = None
    if manifest:
        # Load manifest to make sure it works
        manifest_path = Path(manifest).absolute()
        if not manifest_path.is_file():
            # Look for alias
            if manifest in settings.manifest_alias:
                manifest_path = Path(settings.manifest_alias[manifest])

        manifest = str(manifest_path)
        if not manifest_path.is_file():
            raise UsageError(f"Manifest {manifest} not found")

        Manifest.load(manifest_path, label="host")

    # Update settings
    if settings.MANIFEST:
        reporter.print(f"Was using manifest {settings.MANIFEST}")

    # Save new manifest
    settings.MANIFEST = manifest_path
    if alias:
        if manifest:
            settings.manifest_alias[alias] = manifest
            reporter.print(f'Manifest alias "{alias}" saved')
        else:
            settings.manifest_alias.pop(alias, None)
            reporter.print(f'Manifest alias "{alias}" cleared')
    settings.save()

    if manifest:
        reporter.print(f"Now using manifest {manifest}")
    else:
        reporter.print("Now using no manifest")
