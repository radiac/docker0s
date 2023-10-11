import sys
from functools import update_wrapper
from os import getenv
from pathlib import Path

import click

from .app import BaseApp
from .app.names import normalise_name
from .config import config
from .exceptions import Docker0sException, UsageError
from .manifest import Manifest
from .path import find_manifest
from .reporter import reporter


class ExceptionHandlerGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except Docker0sException as e:
            reporter.error(str(e))
            reporter.error("Operation failed.")
            sys.exit(1)


@click.group(cls=ExceptionHandlerGroup)
@click.option("--config", "-c", "config_path")
@click.option("--manifest", "-m")
@click.option("--debug/--no-debug", "-d", is_flag=True)
@click.pass_context
def cli(
    ctx,
    config_path: str | None = None,
    manifest: str | None = None,
    debug: str | None = None,
):
    ctx.ensure_object(dict)

    # Load config
    with reporter.task("Loading config"):
        config.load(path=config_path, debug=debug)
    reporter.debug(f"Loaded config from {config.path}")

    ctx.obj.update(
        {
            "manifest_raw": manifest,
        }
    )


def with_manifest(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        # Get global context vars
        manifest_raw = ctx.obj.get("manifest_raw") or getenv("DOCKER0S_MANIFEST")

        # Get manifest path
        with reporter.task("Finding host manifest"):
            manifest_path: Path | None = None
            if manifest_raw:
                manifest_path = Path(manifest_raw)

            elif config.manifest_path:
                manifest_path = Path(config.manifest_path)

            else:
                path_dir = Path.cwd()
                manifest_path = find_manifest(path_dir)
                if manifest_path is None:
                    manifest_path = path_dir

        if not manifest_path.is_file():
            raise UsageError(f"Manifest not found at {manifest_path}")
        reporter.debug(f"Using manifest at {manifest_path}")

        # Try to load manifest
        manifest = Manifest.load(manifest_path, label="host")

        ctx.obj.update(
            {
                "manifest": manifest,
                "manifest_path": manifest_path,
            }
        )
        return ctx.invoke(f, ctx.obj["manifest"], *args, **kwargs)

    return update_wrapper(new_func, f)


class Target:
    app: str
    service: str | None

    def __init__(self, app: str, service: str | None = None):
        # Normalise app name and ensure the target string is valid
        if not app:
            app = ""
        app_norm = normalise_name(app)

        if not app_norm and service:
            raise UsageError(f"Invalid target .{service} - app missing")
        self.app = app_norm
        self.service = service

    def __str__(self) -> str:
        if self.service:
            return f"{self.app}.{self.service}"
        return self.app


class TargetParamType(click.ParamType):
    name = "target"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.core.Context | None
    ) -> Target:
        if ctx is not None and ctx.params.get("all_flag", False):
            return self.fail("Cannot specify both --all and targets")

        # TODO: never seems to reach this bracnh
        elif "." in value:
            parts = value.split(".")
            if len(parts) != 2:
                return self.fail(f"{value!r} is not a app.service target", param, ctx)

            app_name, service_name = parts
        else:
            app_name = value
            service_name = None
        return Target(app=app_name, service=service_name)


class TargetManager:
    manifest: Manifest
    targets = tuple[Target]
    apps: list[BaseApp]
    app_lookup: dict[str, BaseApp]
    service_lookup: dict[BaseApp, list[str]]

    def __init__(self, manifest: Manifest, targets: tuple[Target, ...]):
        self.manifest = manifest
        self.targets = targets

        # Init manifest and prepare lookups
        self.apps = manifest.init_apps(
            *set(target.app for target in targets if target.app)
        )
        self.app_lookup = {app.get_name(): app for app in self.apps}

        # Create service lookup for each app
        self.service_lookup = {}
        for target in targets:
            bound_app: BaseApp = self.app_lookup[target.app]
            if bound_app in self.service_lookup:
                if len(self.service_lookup[bound_app]) == 0:
                    return UsageError(
                        f"Cannot target mix of app {target.app} and service {target}"
                    )
            else:
                self.service_lookup[bound_app] = []

            if target.service is None:
                continue
            self.service_lookup[bound_app].append(target.service)

    def get_app_services(self):
        for app in self.apps:
            yield (app, self.service_lookup.get(app, []))


TARGET_TYPE = TargetParamType()


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
        if not config.manifest_alias:
            reporter.print("No aliases defined")
        else:
            reporter.print("Available aliases:")
            for alias, path in sorted(config.manifest_alias.items()):
                reporter.print(f"  {alias}: {path}")
        return

    if manifest:
        # Load manifest to make sure it works
        manifest_path = Path(manifest).absolute()
        if not manifest_path.is_file():
            # Look for alias
            if manifest in config.manifest_alias:
                manifest_path = Path(config.manifest_alias[manifest])

        manifest = str(manifest_path)
        if not manifest_path.is_file():
            raise UsageError(f"Manifest {manifest} not found")

        Manifest.load(manifest_path, label="host")

    # Update config
    if config.manifest_path:
        reporter.print(f"Was using manifest {config.manifest_path}")

    # Save new manifest
    config.manifest_path = manifest
    if alias:
        if manifest:
            config.manifest_alias[alias] = manifest
            reporter.print(f'Manifest alias "{alias}" saved')
        else:
            config.manifest_alias.pop(alias, None)
            reporter.print(f'Manifest alias "{alias}" cleared')
    config.save()

    if manifest:
        reporter.print(f"Now using manifest {manifest}")
    else:
        reporter.print("Now using no manifest")


from rich.table import Table


@cli.command()
@with_manifest
def ls(manifest: Manifest):
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

    app: type[BaseApp]
    app_names = [app.get_docker_name() for app in manifest.apps]
    table.add_row("Apps", "\n".join(app_names))

    reporter.print(table)


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


def invoke():
    cli(obj={})
