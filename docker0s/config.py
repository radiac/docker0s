from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import get_type_hints

from .exceptions import DefinitionError, UsageError


@dataclass
class Config:
    path: Path
    manifest_path: str | None = None
    manifest_alias: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Config:  # TODO: change to Self when supported
        with path.open("r") as file:
            raw_data = json.load(file)

        version = raw_data.pop("version", None)
        if version != 1:
            raise UsageError(f"Invalid config file at {path}")

        annotations = get_type_hints(cls)
        safe_data = {}
        for key, value in raw_data.items():
            if key == "path" or key not in annotations:
                raise DefinitionError(f"Unexpected value {key} for {path}")
            safe_data[key] = value

        safe_data["path"] = path

        return cls(**safe_data)

    def save(self):
        # Prep data
        data = asdict(self)
        del data["path"]
        data["version"] = 1

        # Write
        if not self.path.parent.exists():
            self.path.parent.mkdir()

        with self.path.open("w") as file:
            json.dump(data, file)
