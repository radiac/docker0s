from os import getenv
from pathlib import Path


#: Docker0s local path, default ~/.docker0s/
LOCAL_PATH = Path(getenv("DOCKER0S_PATH", "~/.docker0s")).expanduser()

#: Cache dir, default ~/.docker0s/cache/
CACHE_PATH = Path(getenv("DOCKER0S_CACHE_PATH", LOCAL_PATH / "cache")).expanduser()

#: Remote filename for env files
FILENAME_ENV = getenv("DOCKER0S_ENV_FILENAME", "env")

#: Remote filename for compose files (some App class may override)
FILENAME_COMPOSE = getenv("DOCKER0S_COMPOSE_FILENAME", "docker-compose.yml")

#: Remote dir to hold assets
DIR_ASSETS = getenv("DOCKER0S_DIR_ASSETS", "assets")
