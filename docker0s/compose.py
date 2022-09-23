from pathlib import Path
from urllib.parse import urlparse


class Compose:
    def __init__(self, path: Path | str):
        self.path = str(path)
        self.url = urlparse(str(self.path))

    @property
    def is_local(self):
        if self.url.scheme:
            return False
        return True

    def get_local_path(self):
        if self.is_local:
            return self.path

        # TODO
        # pull file to tmp
        # return tmp path
        # need to clean up afterwards - can we do this as a context manager?
