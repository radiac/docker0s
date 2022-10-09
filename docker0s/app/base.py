from __future__ import annotations

import inspect
from pathlib import Path, PosixPath
from typing import Any

from ..env import dump_env, read_env
from ..host import Host
from ..manifest_object import ManifestObject
from ..path import AppPath, ManifestPath
from ..settings import FILENAME_COMPOSE, FILENAME_ENV
from .names import pascal_to_snake


app_registry: dict[str, type[BaseApp]] = {}


class BaseApp(ManifestObject, abstract=True):
    #: Path to the directory containing the app
    #:
    #: For access see ``.get_path``
    #:
    #: Default: same dir as manifest
    path: str | ManifestPath = ""

    #: Path to a base docker0s manifest for this app. This must define a single app with
    #: the same name, and cannot define a host.
    #:
    #: This referenced manifest will will act as the base manifest. That in turn can
    #: reference an additional base manifest.
    #:
    #: Default: ``app://docker0s.py``, then ``app://docker0s.yml``
    extends: str | AppPath | None = None

    # Defaults for ``extends`` - first found will be used
    default_extends: list[str | AppPath] = [
        "app://docker0s.py",
        "app://docker0s.yml",
    ]

    #: Filename for docker-compose definition
    #: Path to the app's docker compose file. This will be pushed to the host.
    #:
    #: For access see ``.get_compose``
    #:
    #: Default: ``app://docker-compose.yml``
    compose: str | AppPath = "app://docker-compose.yml"

    #: File containing environment variables for docker-compose
    #:
    #: Path to an env file, or a list of paths
    #:
    #: For access see ``.get_env_data``
    env_file: str | AppPath | list[str | AppPath] | None = None

    #: Environment variables for docker-compose
    #:
    #: For access see ``.get_env_data``
    env: dict[str, (str | int)] | None = None

    #: If True, COMPOSE_PROJECT_NAME will be automatically added to the env if not
    #: set by ``env_file`` or ``env``
    set_project_name: bool = True

    # Host this app instance is bound to - eg App(host=...)
    host: Host

    def __init_subclass__(
        cls, abstract: bool = False, name: str | None = None, **kwargs
    ):
        """
        Set abstract flag and register abstract classes with the registry
        """
        super().__init_subclass__(abstract=abstract, name=name, **kwargs)

        if abstract:
            global app_registry  # not required, for clarity
            if cls.__name__ in app_registry:
                raise ValueError(
                    f"Abstract class names must be unique, {cls.__name__} is duplicate"
                )
            app_registry[cls.__name__] = cls

    def __init__(self, host: Host):
        self.host = host

    def __str__(self):
        return self.get_name()

    @classmethod
    def get_name(cls) -> str:
        """
        The docker0s name of this app in PascalCase
        """
        return cls.__name__

    @classmethod
    def get_docker_name(cls) -> str:
        """
        The docker container name of this app in snake_case
        """
        return pascal_to_snake(cls.get_name())

    @classmethod
    def get_manifest_path(cls) -> Path:
        """
        Find the path of the manifest file which defined this app.

        If this was pulled from a git repository, this will be the local path.
        """
        cls_module = inspect.getmodule(cls)
        if cls_module is None or cls_module.__file__ is None:
            raise ValueError(f"Cannot find module path for app {cls}")
        return Path(cls_module.__file__)

    @classmethod
    def get_manifest_dir(cls) -> Path:
        return cls.get_manifest_path().parent

    @classmethod
    def get_path(cls) -> ManifestPath:
        """
        Resolve ``cls.path`` to a ``ManifestPath``
        """
        # TODO: Add a test to check this is a dir, not a file?

        path = ManifestPath(cls.path, manifest_dir=cls.get_manifest_dir())
        return path

    @classmethod
    def _mk_app_path(cls, path: str | AppPath) -> AppPath:
        """
        Internal helper for building an AppPath where this is the app
        """
        return AppPath(path, manifest_dir=cls.get_manifest_dir(), app=cls)

    @classmethod
    def _get_base_manifest(cls) -> AppPath | None:
        """
        Find the path to the base manifest if one exists, otherwise return None
        """
        # Find paths to seek
        extends: list[AppPath]
        if cls.extends:
            extends = [cls._mk_app_path(cls.extends)]
        else:
            extends = [cls._mk_app_path(path) for path in cls.default_extends]

        # Return the first which exists
        for path in extends:
            if path.exists():
                return path
        return None

    @classmethod
    def apply_base_manifest(cls):
        """
        If a base manifest can be found by _get_base_manifest, load it and look for a
        BaseApp subclass with the same name as this. If found, add it to the base
        classes for this class.
        """
        path = cls._get_base_manifest()
        if path is None:
            if cls.extends is not None:
                raise ValueError(
                    f"Could not find base manifest {cls.extends} in {cls.path}"
                )
            # Just looking for defaults, ignore
            return

        from ..manifest import Manifest

        base_manifest = Manifest.load(path)
        if base_manifest.host is not None:
            raise ValueError("A base manifest cannot define a host")
        base_app = base_manifest.get_app(cls.get_name())
        if base_app is None:
            raise ValueError(
                f"Base manifest {path} does not define an app called {cls.get_name()}"
            )

        if not issubclass(cls, base_app):
            cls.__bases__ = (base_app,) + cls.__bases__

    @classmethod
    def get_compose(cls) -> AppPath:
        """
        Return an AppPath to the compose file
        """
        return cls._mk_app_path(cls.compose)

    @classmethod
    def get_env_data(cls) -> dict[str, str | int | None]:
        """
        Load env files in order (for key conflicts last wins), and then merge in the env
        dict, if defined
        """
        # Build list of files
        raw_env_files: list[str | AppPath] = []
        if cls.env_file is not None:
            if isinstance(cls.env_file, (tuple, list)):
                raw_env_files = cls.env_file
            else:
                raw_env_files = [cls.env_file]
        env_files: list[AppPath] = [
            cls._mk_app_path(env_file) for env_file in raw_env_files
        ]

        # Prepare dict
        env_dict = cls.env
        if env_dict is None:
            env_dict = {}

        env: dict[str, str | int | None] = read_env(*env_files, **env_dict)

        if cls.set_project_name and "COMPOSE_PROJECT_NAME" not in env:
            env["COMPOSE_PROJECT_NAME"] = cls.get_docker_name()
        return env

    @property
    def remote_path(self) -> PosixPath:
        """
        The remote path for this app
        """
        return self.host.path(self.get_docker_name())

    @property
    def remote_compose(self) -> PosixPath:
        """
        A PosixPath to the remote compose file
        """
        return self.remote_path / FILENAME_COMPOSE

    @property
    def remote_env(self) -> PosixPath:
        """
        A PosixPath for the remote env file
        """
        return self.remote_path / FILENAME_ENV

    def deploy(self):
        """
        Deploy the docker-compose and env files for this app
        """
        print(f"Deploying {self} to {self.host}")
        self.write_env_to_host()
        self.push_compose_to_host()

    def write_env_to_host(self):
        env_dict = self.get_env_data()
        env_str = dump_env(env_dict)
        self.host.write(self.remote_env, env_str)

    def push_compose_to_host(self):
        compose_local: Path = self.get_compose().absolute
        compose_remote: PosixPath = self.remote_compose
        self.host.push(compose_local, compose_remote)

    def call_compose(self, cmd: str, args: dict[str, Any] | None = None):
        """
        Run a docker-compose command on the host
        """
        self.host.call_compose(
            compose=self.remote_compose,
            env=self.remote_env,
            cmd=cmd,
            cmd_args=args,
        )

    def up(self, *services: str):
        """
        Bring up one or more services in this app

        If no services are specified, all services are selected
        """
        if services:
            for service in services:
                self.call_compose("up --build --detach {service}", {"service": service})
        else:
            self.call_compose("up --build --detach")

    def down(self, *services: str):
        """
        Take down one or more containers in this app

        If no services are specified, all services are selected
        """
        if services:
            for service in services:
                self.call_compose(
                    "rm --force --stop -v {service}", {"service": service}
                )
        else:
            self.call_compose("down")

    def restart(self, *services: str):
        """
        Restart one or more services in this app

        If no services are specified, all services are selected
        """
        if services:
            for service in services:
                self.call_compose("restart {service}", {"service": service})
        else:
            self.call_compose("restart")

    def exec(self, service: str, command: str):
        """
        Execute a command in the specified service

        Command is passed as it arrives, values are not escaped
        """
        self.call_compose(f"exec {{service}} {command}", {"service": service})
