from functools import update_wrapper
from pathlib import Path

import click

from .app import BaseApp
from .app.names import normalise_name
from .manifest import Manifest
from .path import ManifestPath


@click.group()
@click.option("--manifest", "-m")
@click.pass_context
def cli(ctx, manifest: str | None = None):
    ctx.ensure_object(dict)

    # Get manifest path
    if manifest:
        path = Path(manifest)
        manifest_file = path.name
        path = path.parent

    else:
        path = Path.cwd()
        if (path / "manifest.py").exists():
            manifest_file = "manifest.py"
        elif (path / "manifest.yml").exists():
            manifest_file = "manifest.yml"
        else:
            raise click.ClickException("Manifest not found")

    manifest_path = ManifestPath(manifest_file, manifest_dir=path)

    # Load manifest
    manifest_obj = Manifest.load(manifest_path)
    ctx.obj["manifest"] = manifest_obj


def with_manifest(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
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
            raise click.UsageError(f"Invalid target .{service} - app missing")
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
                    raise click.UsageError(
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
@with_manifest
def ls(manifest: Manifest):
    """
    List all apps

    Usage:
        docker0s ls
    """
    print(f"{manifest}")
    if manifest.host:
        print(f"Host: {manifest.host()}")
    print("Apps:")
    app: type[BaseApp]
    for app in manifest.apps:
        print(f"  {app.get_name()}")


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
        raise click.UsageError("Must specify --all or one or more apps")

    safe_apps = (normalise_name(app_name) for app_name in apps)
    bound_apps = manifest.init_apps(*safe_apps)
    for app in bound_apps:
        app.deploy()


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
        raise click.UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        app.up(*services)


@cli.command()
@with_manifest
@click.argument("targets", type=TARGET_TYPE, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def down(manifest: Manifest, targets: tuple[Target, ...], all_flag: bool = False):
    if not targets and not all_flag:
        raise click.UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        app.down(*services)


@cli.command()
@with_manifest
@click.argument("targets", type=TARGET_TYPE, required=False, nargs=-1)
@click.option("--all", "-a", "all_flag", is_flag=True)
def restart(manifest: Manifest, targets: tuple[Target, ...], all_flag: bool = False):
    if not targets and not all_flag:
        raise click.UsageError("Must specify --all or one or more targets")

    manager = TargetManager(manifest, targets)
    for app, services in manager.get_app_services():
        app.restart(*services)


@cli.command()
@with_manifest
@click.argument("target", type=str)
@click.argument("command")
def exec(manifest: Manifest, target: Target, command: str):
    if not target.service:
        raise click.UsageError("Must specify an app.service target")
    app = manifest.init_apps(target.app)[0]
    app.exec(service=target.service, command=command)


def invoke():
    cli(obj={})
