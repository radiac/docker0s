"""
Manifest management
"""
from __future__ import annotations

import sys
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import module_from_spec
from inspect import isclass

import yaml

from .app import App, BaseApp, app_registry
from .app.names import normalise_name
from .host import Host
from .path import ManifestPath


class Manifest:
    path: ManifestPath
    apps: list[type[BaseApp]]
    app_lookup: dict[str, type[BaseApp]]
    host: type[Host] | None = None

    def __init__(self, path: ManifestPath):
        self.path = path
        self.apps: list[type[BaseApp]] = []
        self.app_lookup: dict[str, type[BaseApp]] = {}

    def __str__(self) -> str:
        return str(self.path)

    def add_app(self, app: type[BaseApp]) -> None:
        self.apps.append(app)
        self.app_lookup[app.__name__] = app

    def get_app(self, name: str) -> type[BaseApp] | None:
        return self.app_lookup.get(name)

    def prepare(self, history: list[ManifestPath]):
        """
        Prepare apps and host for use

        * Load base manifests for any apps which define an ``extends``
        """
        for app in self.apps:
            app.apply_base_manifest(history=history)

    @classmethod
    def load(
        cls, path: ManifestPath, history: list[ManifestPath] | None = None
    ) -> Manifest:
        if not path.exists():
            raise ValueError(f"Cannot load {path} - file not found")

        if history is None:
            history = []
        if path in history:
            raise ValueError(f"Cannot load {path} - recursive extends detected")
        history.append(path)

        # Load manifest
        if path.filetype == ".py":
            manifest = cls.load_py(path)
        elif path.filetype == ".yml":
            manifest = cls.load_yml(path)
        else:
            raise ValueError(f"Manifest {path} filetype invalid - must be .yml or .py")

        manifest.prepare(history)
        return manifest

    @classmethod
    def load_py(cls, path: ManifestPath) -> Manifest:
        # Load module
        module = SourceFileLoader(
            f"docker0s.manifest.loaded.{path.uuid}",
            str(path.get_local_path()),
        ).load_module()
        setattr(module, "__manifest_path__", path)
        sys.modules[module.__name__] = module

        # Collect apps and hosts
        manifest = Manifest(path)
        for obj in module.__dict__.values():
            if not isclass(obj):
                continue

            if issubclass(obj, BaseApp) and not obj.abstract:
                manifest.add_app(obj)

            elif issubclass(obj, Host) and not obj.abstract:
                if manifest.host is not None:
                    raise ValueError("Cannot define more than one host in a manifest")
                manifest.host = obj

        return manifest

    @classmethod
    def load_yml(cls, path: ManifestPath) -> Manifest:
        local_path = path.get_local_path()
        raw = local_path.read_text()
        data = yaml.safe_load(raw)

        # Validate top level
        apps_raw = data.pop("apps", [])
        host_raw = data.pop("host", None)
        if len(data) > 0:
            raise ValueError(
                f"Error loading {path}: unexpected root elements {', '.join(data.keys())}"
            )
        if not isinstance(apps_raw, dict):
            raise ValueError(
                f"Error loading {path}: expecting root apps definition, found {type(apps_raw)}"
            )
        if host_raw and not isinstance(host_raw, dict):
            raise ValueError(
                f"Error loading {path}: expecting root host definition, found {type(host_raw)}"
            )

        # Create module and start manifest
        module_spec = ModuleSpec(
            f"docker0s.manifest.loaded.{path.uuid}",
            None,
            origin=str(local_path),
        )
        module = module_from_spec(module_spec)
        module.__file__ = str(local_path)
        sys.modules[module.__name__] = module
        manifest = Manifest(path)

        # Apps
        for app_name, app_raw in apps_raw.items():
            if not isinstance(app_raw, dict):
                raise ValueError(
                    f"Error loading {path}: expecting app definition for {app_name}, found {type(app_raw)}"
                )

            # Get app class
            app_type: str = app_raw.pop("type", None)
            app_base_cls: type[BaseApp]
            if app_type is None:
                app_base_cls = App
            else:
                if app_type not in app_registry:
                    raise ValueError(f"Unknown app type {app_type}")
                app_base_cls = app_registry[app_type]

            # Update path
            if "path" not in app_raw:
                app_raw["path"] = str(local_path / "..")

            # YAML supports snake case names because it looks nicer.
            # Convert to PascalCase
            name = normalise_name(app_name)
            if manifest.get_app(name):
                raise ValueError(
                    f"Error loading {path}: normalised name collision: {app_name} and {name} are equivalent"
                )

            # Build app class and add to manifest
            app_cls: type[BaseApp] = app_base_cls.from_dict(
                name=name, module=module.__name__, data=app_raw
            )
            setattr(module, name, app_cls)
            manifest.add_app(app_cls)

        # Host
        if host_raw:
            manifest.host = Host.from_dict(
                name="ImportedHost", module=module.__name__, data=host_raw
            )

        return manifest

    def init_apps(self, *app_names: str) -> list[BaseApp]:
        """
        Given one or more names of apps, find them in the registry and initialise them
        with the manifest host
        """
        # Prepare the host
        if not self.host:
            raise ValueError("Cannot initialise a manifest that has no host")
        # Per-exec host options can be added here later
        host = self.host()

        # Find app classes
        app_classes: list[type[BaseApp]]
        if not app_names:
            app_classes = self.apps
        else:
            app_classes = []
            for app_name in app_names:
                app_cls: type[BaseApp] | None = self.get_app(app_name)
                if app_cls is None:
                    raise ValueError(f"Unknown app name {app_name}")
                app_classes.append(app_cls)

        # Initialise the apps
        apps: list[BaseApp] = []
        for app_cls in app_classes:
            apps.append(app_cls(host=host))

        return apps
