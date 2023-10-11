from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from os import getenv
from pathlib import Path
from typing import get_type_hints

import click

from .exceptions import DefinitionError, UsageError
from .reporter import reporter


@dataclass
class Config:
    path: Path = Path(
        getenv("DOCKER0S_CONFIG", Path(click.get_app_dir("docker0s")) / "config.json")
    )
    manifest_path: str | None = None
    manifest_alias: dict[str, str] = field(default_factory=dict)

    def __init__(self):
        self._session = {
            "debug": getenv("DOCKER0S_DEBUG", "false").lower()
            not in ("false", "off", "no"),
        }

    def load(self, path: Path | str | None = None, **session_data):
        if path is not None:
            self.path = Path(path)

        if not self.path.is_file():
            raise UsageError(f"Config file not found at {self.path}")

        with self.path.open("r") as file:
            raw_data = json.load(file)

        version = raw_data.pop("version", None)
        if version != 1:
            raise UsageError(f"Invalid config file at {self.path}")

        annotations = get_type_hints(type(self))
        for key, value in raw_data.items():
            if key == "path" or key not in annotations:
                raise DefinitionError(f"Unexpected value {key} for {self.path}")
            setattr(self, key, value)

        self.session(**session_data)

        # Configure reporter from here to avoid circular import
        reporter.can_debug = self.debug

    def __getattribute__(self, item):
        if item != "_session" and item in self._session:
            return self._session[item]
        else:
            return super().__getattribute__(item)

    def session(self, **session_data):
        self._session.update(session_data)

    def save(self):
        if self.path is None:
            raise UsageError("Cannot save config without a path")

        # Prep data
        data = asdict(self)
        del data["path"]
        data["version"] = 1

        # Write
        if not self.path.parent.exists():
            self.path.parent.mkdir()

        with self.path.open("w") as file:
            json.dump(data, file)


config = Config()
