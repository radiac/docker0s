from os import getenv
from pathlib import Path


#: Docker0s local path, default ~/.docker0s/
LOCAL_PATH = Path(getenv("DOCKER0S_PATH", "~/.docker0s")).expanduser()

#: Cache dir, default ~/.docker0s/cache/
CACHE_PATH = Path(getenv("DOCKER0S_CACHE_PATH", LOCAL_PATH / "cache")).expanduser()
