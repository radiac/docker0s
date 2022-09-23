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
