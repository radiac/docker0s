"""
Commands which operate on the host
"""

import click

from ..app.names import normalise_name
from ..exceptions import UsageError
from ..manifest import Manifest
from ..reporter import reporter
from .core import TARGET_TYPE, Target, TargetManager, cli, with_manifest


@cli.command()
@with_manifest
@click.argument("apps", type=str, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def deploy(manifest: Manifest, apps: tuple[str], all_flag: bool = False):
    """
    Deploy one or more apps

    Usage:
        docker0s deploy myapp
        docker0s deploy traefik website
        docker0s deploy --all
    """
    if not apps and not all_flag:
        raise UsageError("Must specify --all or one or more apps")

    safe_apps = (normalise_name(app_name) for app_name in apps)
    bound_apps = manifest.init_apps(*safe_apps)
    for app in bound_apps:
        reporter.debug(f"Deploying {app.get_docker_name()}")
        app.deploy()
        reporter.debug(f"Deployed {app.get_docker_name()}")


@cli.command()
@with_manifest
@click.argument("targets", type=TARGET_TYPE, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def up(manifest: Manifest, targets: tuple[Target, ...], all_flag: bool = False):
    """
    Bring up all containers for one or more apps or services:
        docker0s up myapp
        docker0s up traefik website.backend

    Bring up all containers for all apps:
        docker0s deploy --all
    """
    if not targets and not all_flag:
        raise UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        reporter.debug(f"Bringing up {app.get_docker_name()} {services=}")
        app.up(*services)
        reporter.debug(f"Brought up {app.get_docker_name()} {services=}")


@cli.command()
@with_manifest
@click.argument("targets", type=TARGET_TYPE, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def down(manifest: Manifest, targets: tuple[Target, ...], all_flag: bool = False):
    if not targets and not all_flag:
        raise UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        reporter.debug(f"Taking down {app.get_docker_name()} {services=}")
        app.down(*services)
        reporter.debug(f"Took down {app.get_docker_name()} {services=}")


@cli.command()
@with_manifest
@click.argument("targets", type=TARGET_TYPE, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def restart(manifest: Manifest, targets: tuple[Target, ...], all_flag: bool = False):
    if not targets and not all_flag:
        raise UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        reporter.debug(f"Restarting {app.get_docker_name()} {services=}")
        app.restart(*services)
        reporter.debug(f"Restarted {app.get_docker_name()} {services=}")


@cli.command()
@with_manifest
@click.argument("target", type=TARGET_TYPE)
@click.argument("command", type=str)
def exec(manifest: Manifest, target: Target, command: str):
    if not target.service:
        raise UsageError("Must specify an app.service target")
    app = manifest.init_apps(target.app)[0]
    reporter.debug(f"Executing remote command in {target.app}.{target.service}")
    app.exec(service=target.service, command=command)
    reporter.debug(f"Execution complete")


@cli.command()
@with_manifest
def status(manifest: Manifest):
    if not manifest.host:
        raise UsageError("No host found in manifest")

    host = manifest.init_host()
    reporter.debug("Retrieving status")
    result = host.exec(cmd="docker ps --all", verbose=False)
    reporter.print(result.stdout)


@cli.command()
@with_manifest
@click.argument("target", type=TARGET_TYPE)
def logs(manifest: Manifest, target: Target):
    if not target.service:
        raise UsageError("Must specify an app.service target")
    reporter.debug("Retrieving logs")
    app = manifest.init_apps(target.app)[0]
    app.logs(service=target.service)
