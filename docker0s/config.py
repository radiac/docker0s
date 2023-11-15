"""
Load and save the config file, and manage settings

Config file format:

    {
        "settings": {...},      // Lowercase versions of the uppercase settings
        "manifest_alias": {..}, // Aliases for manifests
    }
"""
from __future__ import annotations

import json
from functools import wraps
from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING, Any, get_type_hints

import platformdirs

from .exceptions import DefinitionError, ExecutionError, UsageError


if TYPE_CHECKING:
    from .cache import CacheState


# Suffix for manifest lockfile, if one is not provided
LOCKFILE_SUFFIX = ".lock"

# Filename for the state file within the cache
CACHE_STATE = "state.json"

# Remote filenames
REMOTE_ENV: str = "env"
REMOTE_COMPOSE: str = "docker-compose.yml"
REMOTE_ASSETS: str = "assets"

# Current config file format version
CURRENT_VERSION = 2


class SettingsOverride:
    settings: Settings
    overrides: dict[str, Any]
    originals: dict[str, Any]

    def __init__(self, settings, **overrides):
        self.settings = settings
        self.overrides = {k.upper(): v for k, v in overrides.items()}
        self.originals = {}

    def __enter__(self):
        self.override()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore()

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            self.override()
            result = fn(*args, **kwargs)
            self.restore()
            return result

        return wrapper

    def override(self):
        self.settings._overrides = self.overrides

    def restore(self):
        self.settings._overrides = {}


class Settings:
    #: Values in config file
    _store: dict[str, Any]

    #: Values from env vars
    _env: dict[str, Any]

    #: Values from cli
    _options: dict[str, Any]

    #: Temporary override values
    _overrides: dict[str, Any]

    # Default settings configurable by env vars and some command options
    #
    #: Path to config file
    CONFIG: Path = (
        platformdirs.user_config_path(appname="docker0s", ensure_exists=True)
        / "config.json"
    )

    #: Path to host manifest
    MANIFEST: Path | None = None

    #: Path to manifest lockfile
    LOCKFILE: Path | None = None

    #: Path to cache dir
    CACHE_PATH: Path = platformdirs.user_cache_path(
        appname="docker0s", ensure_exists=True
    )
    #: Enable caching
    CACHE_ENABLED: bool = False

    #: Maximum cache age, in seconds
    CACHE_AGE: int = 60

    #: Enable debugging
    DEBUG: bool = False

    # Saved attributes not from env/cli
    manifest_alias: dict[str, str]

    # Session attributes
    _cache_state: Any = None  # CacheState, but can't specify due to get_type_hints

    def __init__(self):
        self._store = {}
        self._env = {}
        self._options = {}
        self._overrides = {}
        self.manifest_alias = {}
        self.load_env()

    def keys(self):
        return [name for name in dir(self) if name.isupper()]

    def _cast(self, name, value):
        if value is None:
            return value

        cast_fn = getattr(self, f"_cast_{name}", None)
        if not cast_fn:
            # Use annotation to cast

            annotations = get_type_hints(type(self))
            cast_fn = annotations[name]

            if (
                cast_fn is bool
                and isinstance(value, str)
                and value.lower() in ["false", "off", "0"]
            ):
                value = False

        return cast_fn(value)

    def _cast_MANIFEST(self, value):
        if value is None:
            return None
        return Path(value)

    def load_env(self):
        for name in self.keys():
            value = getenv(f"DOCKER0S_{name}", None)
            if value is None:
                continue
            self._env[name] = self._cast(name, value)

    def options(self, **options):
        for key, value in options.items():
            setting_name = key.upper()
            if setting_name not in dir(self):
                raise DefinitionError(f"Unexpected option {key}")
            self._options[setting_name] = value

    def __getattribute__(self, name) -> Any:
        if name.isupper() and name in self.keys():
            value = (
                self._overrides.get(name)
                or self._options.get(name)
                or self._env.get(name)
                or self._store.get(name)
            )
            if value:
                return value

        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name.isupper() and name in self.keys():
            self._options[name] = self._cast(name, value)
            return
        return super().__setattr__(name, value)

    def load(self, **options):
        self.options(**options)
        path = self.CONFIG

        if not path.is_file():
            raise UsageError(f"Config file not found at {path}")

        with path.open("r") as file:
            raw_data = json.load(file)

        # Extract key data
        version = raw_data.pop("version", CURRENT_VERSION)
        settings = raw_data.pop("settings", {})
        self.manifest_alias = raw_data.pop("manifest_alias", {})

        # Upgrade config file
        if version == 1:
            # Shift settings up from root
            settings = {
                "manifest": raw_data.pop("manifest_path", None),
            }
        elif version == 2:
            pass
        else:
            raise UsageError(f"Invalid config file at {path}")

        for key, value in settings.items():
            upper_key = key.upper()
            if not key.islower() or upper_key not in dir(self):
                raise DefinitionError(f"Unexpected config settings.{key}")
            self._store[upper_key] = self._cast(upper_key, value)

    def save(self):
        path = self.CONFIG
        if path is None:
            raise UsageError("Cannot save config without a path")

        # Prep data
        store = {
            key.lower(): str(value) if isinstance(value, Path) else value
            for key, value in self._store.items()
        }
        data = {
            "version": CURRENT_VERSION,
            "settings": store,
            "manifest_alias": self.manifest_alias,
        }
        # Write
        if not path.parent.exists():
            path.parent.mkdir()

        with path.open("w") as file:
            json.dump(data, file)

    def override(self, **overrides):
        """
        Decorator to override settings for the duration of a function
        """
        return SettingsOverride(self, **overrides)

    def store(self, name: str, value: str | None = None):
        """
        Store a setting

        Setting name must be uppercase
        """
        if name not in dir(self):
            raise ExecutionError(f"Unexpected setting {name}")

        if value is None:
            if name in self._store:
                del self._store[name]
            return

        self._store[name] = self._cast(name, value)
        self.save()

    def get_cache_state(self) -> CacheState:
        """
        Initialise the cache state once

        If using threading, this must be called before any threads are started. This is
        handled by workers.Workers automatically
        """
        from .cache import CacheState

        if self._cache_state is None:
            self._cache_state = CacheState.from_file(self.CACHE_PATH / CACHE_STATE)
        return self._cache_state


settings = Settings()
