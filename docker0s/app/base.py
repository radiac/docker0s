from __future__ import annotations

import inspect
from pathlib import Path, PosixPath
from typing import Any, Callable

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..env import dump_env, read_env
from ..exceptions import DefinitionError
from ..host import Host
from ..manifest_object import ManifestObject
from ..path import ExtendsPath
from ..settings import DIR_ASSETS, FILENAME_COMPOSE, FILENAME_ENV
from .names import normalise_name, pascal_to_snake


# Abstract app registry for type lookups
abstract_app_registry: dict[str, type[BaseApp]] = {}


class AppsTemplateContext:
    """
    Lazy context getter for use in template context `apps`
    """

    apps: dict[str, BaseApp]

    def __init__(self, apps: dict[str, BaseApp]):
        self.apps = apps

    def __getitem__(self, name: str) -> dict[str, Any]:
        return self.get(name)

    def __getattr__(self, name: str) -> dict[str, Any]:
        return self.get(name)

    def get(self, name: str) -> dict[str, Any]:
        normalised = normalise_name(name)
        if normalised not in self.apps:
            raise DefinitionError(f"Unknown app {name} ({normalised})")
        return self.apps[normalised].get_compose_context()

    def __contains__(self, name: str) -> bool:
        normalised = normalise_name(name)
        return normalised in self.apps


class EnvTemplateContext:
    """
    Lazy context getter for use in template context `env`
    """

    app: BaseApp

    def __init__(self, app: BaseApp):
        self.app = app

    def __getitem__(self, name: str) -> Any:
        return self.get(name)

    def __getattr__(self, name: str) -> Any:
        return self.get(name)

    def get(self, name: str) -> Any:
        env_data = self.app.get_host_env_data()
        return env_data[name]

    def __contains__(self, name: str) -> bool:
        env_data = self.app.get_host_env_data()
        return name in env_data


class BaseApp(ManifestObject, abstract=True):
    _file: Path  # Path to this manifest file
    _dir: Path  # Path to this manifest file

    #: Path to a base docker0s manifest for this app.
    #:
    #: If the path ends ``::<name>`` it will look for an app definition with that name,
    #: eg ``bases.py::Store``. Otherwise it will look for an app with the same
    #: name as this.
    #:
    #: The base manifest must not define a host.
    #:
    #: This referenced manifest will will act as the base manifest. That in turn can
    #: reference an additional base manifest.
    #:
    #: Default: ``d0s-manifest.py``, then ``d0s-manifest.yml``
    extends: str | None = None
    _extends_path: ExtendsPath | None = None  # Resolved path

    #: Path to the app's docker compose file. This will be pushed to the host.
    #:
    #: This can be a ``.yml`` file, or a ``.jinja2`` template.
    #:
    #: For access see ``.get_compose_path``
    #:
    #: Default: ``docker-compose.jinja2``, then ``docker-compose.yml``
    compose: str | None = None

    COMPOSE_DEFAULTS = [
        "docker-compose.j2",
        "docker-compose.jinja2",
        "docker-compose.yml",
        "docker-compose.yaml",
    ]

    #: Context for docker-compose Jinja2 template rendering
    #:
    #: To add instance data, override ``.get_compose_context``
    compose_context: dict[str, Any] | None = None

    #: File containing environment variables for docker-compose
    #:
    #: Path to an env file, or a list of paths
    #:
    #: For access see ``.get_env_data``
    env_file: str | list[str] | None = None

    #: Environment variables for docker-compose
    #:
    #: For access see ``.get_env_data``
    env: dict[str, (str | int)] | None = None

    #: If True, COMPOSE_PROJECT_NAME will be automatically added to the env if not
    #: set by ``env_file`` or ``env``
    set_project_name: bool = True

    # Host this app instance is bound to on initialisation
    host: Host

    # All app instances defined in the manifest which defines this app, including self
    manifest_apps: dict[str, BaseApp]

    def __init_subclass__(
        cls,
        abstract: bool = False,
        name: str | None = None,
        path: Path | None = None,
        **kwargs,
    ):
        """
        Set abstract flag and register abstract classes with the registry
        """
        super().__init_subclass__(abstract=abstract, name=name, **kwargs)

        if abstract:
            global abstract_app_registry  # not required, for clarity
            if cls.__name__ in abstract_app_registry:
                raise DefinitionError(
                    f"Abstract class names must be unique, {cls.__name__} is duplicate"
                )
            abstract_app_registry[cls.__name__] = cls
            return

        # Detect manifest path
        if path:
            cls._file = path
        else:
            cls_module = inspect.getmodule(cls)
            if cls_module is None or cls_module.__file__ is None:
                # This shouldn't happen
                raise ValueError(f"Cannot find module path for app {cls}")
            cls._file = Path(cls_module.__file__)

        cls._dir = cls._file.parent

    def __init__(self, host: Host):
        self.host = host
        self.other_apps: dict[str, BaseApp] = {}

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
    def apply_base_manifest(cls, history: list[Path] | None = None):
        """
        If a base manifest can be found by _get_base_manifest, load it and look for a
        BaseApp subclass with the same name as this. If found, add it to the base
        classes for this class.
        """
        # Avoid import loop
        from ..manifest import Manifest

        if not cls.extends:
            return

        if not cls._extends_path:
            cls._extends_path = ExtendsPath(cls.extends, cls._dir)

        path = cls._extends_path.get_manifest()

        base_manifest = Manifest.load(path, history)
        if base_manifest.host is not None:
            raise DefinitionError("A base manifest cannot define a host")

        base_name = cls._extends_path.name or cls.get_name()
        base_app = base_manifest.get_app(base_name)
        if base_app is None:
            raise DefinitionError(
                f"Base manifest {path} does not define an app called {base_name}"
            )

        if not issubclass(cls, base_app):
            cls.__bases__ = (base_app,) + cls.__bases__

    @classmethod
    def find_relative_file(
        cls,
        attr: str,
        defaults: list[str] | None = None,
    ) -> tuple[Path, str]:
        """
        Return first file found, or raises DefinitionError
        """
        cls_values: list[tuple[type[BaseApp], Any]] = cls.collect_attr(attr)
        for mro_cls, val in cls_values:
            if val:
                # Value was specified, file should exist
                path = mro_cls._dir / val
                if not path.exists():
                    raise DefinitionError(
                        f'App setting {cls.get_name()}.{attr} specified as "{val}"'
                        f' but "{path}" does not exist'
                    )
                    break
                return mro_cls._dir, val

            elif defaults:
                # Look for defaults
                for filename in defaults:
                    if (mro_cls._dir / filename).exists():
                        return mro_cls._dir, filename

        raise DefinitionError(
            f"App setting {cls.get_name()}.{attr} not specified, no default found"
        )

    @classmethod
    def find_file(
        cls,
        attr: str,
        defaults: list[str] | None = None,
    ) -> Path:
        path, filename = cls.find_relative_file(attr, defaults)
        return path / filename

    @classmethod
    def collect_attr(cls, attr: str) -> list[tuple[type[BaseApp], Any]]:
        """
        Collect attributes directly from the class and its bases, bypassing inheritance
        and returning a list of ``(cls, *values)`` pairs.

        Abstract classes are ignored.

        This is primarily used where we need context of the value definition - ie a path
        relative to the manifest where the path is set, or for env var resolution.
        """
        # TODO: This is a bit of a confusing approach. Because ``extends`` is adding to
        # the base classes to make it easy for us to inherit custom values and functions
        # from parent apps, we need this odd way to collect values bypassing
        # inheritance. This is unexpected magic.
        #
        # Two better options for a future refactor:
        #
        # 1. Resolve relative paths as soon as the class is defined. This makes sense -
        #    at end of __init_subclass__ we could go through and resolve all the paths
        #    and envs, then we can have normal inheritance working as expected.
        #
        #    The disadvantage is we'll need to resolve everything every time we load a
        #    manifest - and that probably includes resolving env vars. We're generally
        #    not worried about speed in docker0s, but this could easily balloon to be a
        #    problem.
        #
        # 2. Don't inject extended classes as base classes. This may be the better
        #    option - we can keep the JIT evaluation of things we may no need, and base
        #    class creation and injection is verging on too magical for this sort of
        #    project.
        #
        #    Instead we could just create a list of app classes that the host manifest
        #    extends, and iterate through them.  This fn would still exist, but it would
        #    be looking at a ``cls._extend_cls_list`` list instead of ``cls.mro()``.
        #
        #    The disadvantage is we'll lose the ability to reference fns in parent
        #    classes by inheritance - most importantly, deployment hooks. This felt like
        #    it would be a big deal early on, but it seems to be an edge case in the
        #    real world - very few projects have needed custom deployment steps, and I
        #    suspect those could all be handled by actual importing and subclassing.
        results: list[tuple[type[BaseApp], Any]] = []
        for mro_cls in cls.mro():
            if not issubclass(mro_cls, BaseApp) or mro_cls.abstract:
                # We're only interested in concrete App classes
                continue
            results.append((mro_cls, mro_cls.__dict__.get(attr, None)))
        return results

    @classmethod
    def get_compose_path(cls) -> Path:
        return cls.find_file(
            attr="compose",
            defaults=cls.COMPOSE_DEFAULTS,
        )

    @classmethod
    def get_env_data(cls) -> dict[str, str | int | None]:
        """
        Load env files in order (for key conflicts last wins), and then merge in the env
        dict, if defined
        """
        attrs_env: list[tuple[type[BaseApp], Any]] = cls.collect_attr("env")
        attrs_env_file: list[tuple[type[BaseApp], Any]] = cls.collect_attr("env_file")
        attrs = reversed(list(zip(attrs_env, attrs_env_file)))

        env: dict[str, str | int | None] = {}
        env_dict: dict
        env_file: list | str
        for (mro_cls, env_dict), (_, env_file) in attrs:
            # Build list of files
            raw_env_files: list[str] = []
            if env_file is not None:
                if isinstance(env_file, (tuple, list)):
                    raw_env_files = env_file
                else:
                    raw_env_files = [env_file]
            env_files: list[Path] = [
                mro_cls._dir / env_file for env_file in raw_env_files
            ]

            # Prepare dict
            if env_dict is None:
                env_dict = {}

            env.update(read_env(*env_files, **env_dict))

        if cls.set_project_name and "COMPOSE_PROJECT_NAME" not in env:
            env["COMPOSE_PROJECT_NAME"] = cls.get_docker_name()
        return env

    @staticmethod
    def command(fn):
        fn.is_command = True
        return fn

    def get_command(self, name: str) -> Callable:
        """
        Return the specified command
        """
        attr = getattr(self, name)
        if callable(attr) and hasattr(attr, "is_command"):
            return attr
        raise ValueError(f"Command {name} not found")

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

    @property
    def remote_assets(self) -> PosixPath:
        """
        A PosixPath for the remote assets dir

        Assets are resources pushed to the server as part of the docker0s deployment -
        config files, scripts, media etc
        """
        return self.remote_path / DIR_ASSETS

    @property
    def remote_store(self) -> PosixPath:
        """
        A PosixPath for the remote store dir

        The store is for files created by the containers - logs, databases, uploads etc
        """
        return self.remote_path / "store"

    def get_compose_context(self, **kwargs: Any) -> dict[str, Any]:
        """
        Build the template context for the compose template
        """
        context = {
            "host": self.host,
            "env": EnvTemplateContext(self),
            "apps": AppsTemplateContext(self.manifest_apps),
            # Reserved for future expansion
            "docker0s": NotImplemented,
            "globals": NotImplemented,
            **kwargs,
        }

        if self.compose_context is not None:
            context.update(self.compose_context)

        return context

    def get_compose_content(self, context: dict[str, Any] | None = None) -> str:
        """
        Return the content for the docker-compose file

        This will either be rendered from ``compose_template`` if it exists, otherwise
        it will be read from ``compose``
        """
        compose_path = self.get_compose_path()
        filetype = compose_path.suffix.lower()
        if filetype == ".yml":
            return compose_path.read_text()

        elif filetype == ".jinja2":
            env = Environment(
                loader=FileSystemLoader(compose_path.parent),
                autoescape=select_autoescape(),
            )

            context = self.get_compose_context(**(context or {}))
            template = env.get_template(compose_path.name)
            return template.render(context)

        raise ValueError(f"Unrecognised compose filetype {filetype}")

    def get_host_env_data(self) -> dict[str, str | int | None]:
        """
        Build the env data dict to be sent to the server
        """
        env_data = self.get_env_data()
        env_data.update(
            {
                "ENV_FILE": str(self.remote_env),
                "ASSETS_PATH": str(self.remote_assets),
                "STORE_PATH": str(self.remote_store),
            }
        )
        return env_data

    def deploy(self):
        """
        Deploy the env file for this app
        """
        self.push_compose_to_host()
        self.write_env_to_host()
        self.host.ensure_parent_path(self.remote_store)

    def push_compose_to_host(self):
        compose_content: str = self.get_compose_content()
        compose_remote: PosixPath = self.remote_compose
        self.host.write(compose_remote, compose_content)

    def write_env_to_host(self):
        env_dict = self.get_host_env_data()
        env_str = dump_env(env_dict)
        self.host.write(self.remote_env, env_str)

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

    def logs(self, service: str):
        """
        Retrieve logs for the given service
        """
        self.call_compose("logs {service}", {"service": service})

    def exec(self, service: str, command: str):
        """
        Execute a command in the specified service

        Command is passed as it arrives, values are not escaped
        """
        self.call_compose(f"exec {{service}} {command}", {"service": service})
