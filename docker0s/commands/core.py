"""
Core command logic - root click element, handlers and common utility functions
"""
import sys
from functools import update_wrapper
from pathlib import Path

import click

from .. import __version__
from ..app import BaseApp
from ..app.names import normalise_name
from ..config import settings
from ..exceptions import Docker0sException, UsageError
from ..manifest import Manifest
from ..path import find_manifest
from ..reporter import reporter


class ExceptionHandlerGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except Docker0sException as e:
            reporter.error(str(e))
            reporter.error("Operation failed.")
            sys.exit(1)


@click.group(cls=ExceptionHandlerGroup)
@click.option("--config", "-c", "config_path", help="Path to config file")
@click.option("--manifest", "-m", "manifest_path", help="Path to host manifest")
@click.option(
    "--cache/--no-cache", "cache_enabled", is_flag=True, help="Enable caching"
)
@click.option("--cache-path", "cache_path", help="Path to cache dir")
@click.option(
    "--cache-age", "cache_age", type=str, help="Maximum cache age, in seconds"
)
@click.option("--debug/--no-debug", "-d", is_flag=True, help="Show debug messages")
@click.version_option(prog_name="docker0s", version=__version__)
@click.pass_context
def cli(
    ctx,
    config_path: str | None = None,
    manifest_path: str | None = None,
    cache_enabled: bool = False,
    cache_path: str | None = None,
    cache_age: int | None = None,
    debug: bool | None = None,
):
    ctx.ensure_object(dict)

    # Load config.
    #
    # This has to happen before anything calls reporter.debug - see reporter.debug for
    # details.
    with reporter.task("Loading config"):
        settings.load(
            config=config_path,
            manifest=manifest_path,
            cache_enabled=cache_enabled,
            cache_path=cache_path,
            cache_age=cache_age,
            debug=debug,
        )
    reporter.debug(f"Loaded config from {settings.CONFIG}")

    ctx.obj.update(
        {
            "manifest_raw": manifest_path,
        }
    )


def with_manifest(fn=None, **setting_overrides):
    def wrapper(fn):
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            # Get global context vars
            manifest_path = settings.MANIFEST

            # Get manifest path
            with reporter.task("Finding host manifest"):
                if manifest_path is None:
                    path_dir = Path.cwd()
                    manifest_path = find_manifest(path_dir)
                    if manifest_path is None:
                        manifest_path = path_dir

            if not manifest_path.is_file():
                raise UsageError(f"Manifest not found at {manifest_path}")
            reporter.debug(f"Using manifest at {manifest_path}")

            # Try to load manifest
            with settings.override(**setting_overrides):
                manifest = Manifest.load(manifest_path, label="host")

            ctx.obj.update(
                {
                    "manifest": manifest,
                    "manifest_path": manifest_path,
                }
            )
            return ctx.invoke(fn, ctx.obj["manifest"], *args, **kwargs)

        return update_wrapper(new_func, fn)

    if fn is not None:
        return wrapper(fn)
    return wrapper


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

        # TODO: never seems to reach this branch
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
                    raise UsageError(
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


def humanise_filesize(size: float):
    for unit in ("B", "KB", "MB"):
        if size < 1024.0:
            return f"{size:3.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} GB"


def humanise_plural(num: int, word: str):
    return word if num == 1 else f"{word}s"


def humanise_timestamp(timestamp: int):
    for limit, unit in ((60, "second"), (60, "minute"), (24, "hour")):
        if timestamp < limit:
            return f"{timestamp} {humanise_plural(timestamp, unit)}"
        timestamp //= limit
    return f"{timestamp} {humanise_plural(timestamp, 'day')}"


def invoke():
    cli(obj={})
