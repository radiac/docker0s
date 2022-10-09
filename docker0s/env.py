from __future__ import annotations

from typing import TYPE_CHECKING

from dotenv import dotenv_values


if TYPE_CHECKING:
    from .path import ManifestPath


def read_env(*paths: ManifestPath, **values: str | int) -> dict[str, str | int | None]:
    """
    Read env vars from one or more manifest paths and update it with a dict
    """
    env: dict[str, str | int | None] = {}
    for path in paths:
        handle = path.stream_text()
        file_values = dotenv_values(stream=handle)
        env.update(file_values)
        handle.close()

    env.update(values)

    return env


def dump_env(env: dict[str, str | int | None]) -> str:
    """
    Convert an env dict into a multi-line string
    """
    lines = []
    for key, val in env.items():
        if val is None:
            lines.append(key)
        elif isinstance(val, int):
            lines.append(f"{key}={val}")
        else:
            escaped = val.replace('"', r"\"")
            lines.append(f'{key}="{escaped}"')
    return "\n".join(lines)
