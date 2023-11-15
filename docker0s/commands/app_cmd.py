"""
App commands
"""

import click

from ..app.names import normalise_name
from ..exceptions import UsageError
from ..manifest import Manifest
from ..reporter import reporter
from .core import TARGET_TYPE, Target, TargetManager, cli, with_manifest


@cli.command()
@with_manifest
@click.argument("target", type=Target)
@click.argument("command", type=str)
@click.argument("arguments", nargs=-1, type=str)
def cmd(manifest: Manifest, target: Target, command: str, arguments: list[str]):
    if target.service:
        raise UsageError("Must specify an app target, not an app.service")
    app = manifest.init_apps(target.app)[0]
    reporter.debug(f"Running local command {target} {command}")
    cmd_fn = app.get_command(command)
    cmd_fn(*arguments)
