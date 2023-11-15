"""
Manifest management commands
"""
from typing import TYPE_CHECKING, Self

import click
from rich.console import Group
from rich.table import Table
from rich.tree import Tree

from ..manifest import Manifest
from ..reporter import reporter
from .core import cli, with_manifest


if TYPE_CHECKING:
    from rich.console import RenderableType


class BaseAppTree(Tree):
    @classmethod
    def from_manifest(cls, manifest: Manifest) -> Self:
        from ..app import BaseApp

        tree = cls(str(manifest.path))
        for root_app in manifest.apps:
            # Find all base paths
            apps: list[tuple[type[BaseApp], Tree]] = [(root_app, tree)]
            while apps:
                app, tree_node = apps.pop()
                branch_node = tree_node.add(cls.render_app(app))
                apps.extend(
                    [
                        (base, branch_node)
                        for base in app.__bases__
                        if issubclass(base, BaseApp) and not base.abstract
                    ]
                )
        return tree

    @classmethod
    def render_app(cls, app):
        return str(app)


class LsAppTree(BaseAppTree):
    @classmethod
    def render_app(cls, app):
        parts = [app.get_docker_name()]
        origin = app.manifest.origin
        if origin:
            parts.append(f"[green]{app.manifest.origin}")
        return "\n".join(parts)


@cli.command()
@click.option(
    "--long",
    "-l",
    is_flag=True,
    default=False,
    help="Show long listing format, expanding app inheritance",
)
@with_manifest
def ls(manifest: Manifest, long=False):
    """
    List all apps

    Usage:
        docker0s ls
    """
    table = Table(show_header=False, show_lines=True)
    table.add_column("Category", style="bold", no_wrap=True)
    table.add_column("Details")

    table.add_row("Manifest", str(manifest.path))
    if manifest.host:
        table.add_row("Host", str(manifest.host()))

    app_names: RenderableType
    if long:
        tree = LsAppTree.from_manifest(manifest)
        app_names = Group(*tree.children)
    else:
        app_names = "\n".join([app.get_docker_name() for app in manifest.apps])
    table.add_row("Apps", app_names)

    reporter.print(table)


@cli.command()
@click.argument("app", required=False)
@click.argument("hash", required=False)
@click.option("--show","show_flag", is_flag=True)
@with_manifest
def lock(manifest: Manifest, app:str|None=None, hash:str|None=None, show_flag:bool=False):
    """
    Lock an app's remote base to a specific version

    Show lock information::

        docker0s lock --show

    Lock all apps::

        docker0s lock --all

    Lock an app::

        docker0s lock <app> [<hash>]
    """
    if show_flag:
        # List lockfiles

    # Find target

    if not app:
        # List
        pass
    else:
        # Get current hash of base
        # Lock app to hash