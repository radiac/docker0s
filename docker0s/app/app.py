from pathlib import Path, PosixPath

from .base import BaseApp


class App(BaseApp, abstract=True):
    """
    A self-contained docker-compose file which deploys containers without additional
    resources
    """

    #: Assets to upload next to the docker-compose.yml
    assets: str | list[str] | None = None

    def deploy(self):
        """
        Deploy the docker-compose and assets for this app
        """
        super().deploy()
        self.push_compose_to_host()
        self.push_assets_to_host()

    def push_compose_to_host(self):
        compose_local: Path = self.get_compose().absolute
        compose_remote: PosixPath = self.remote_compose
        self.host.push(compose_local, compose_remote)

    def push_assets_to_host(self):
        if not self.assets:
            return
        assets = self.assets
        if isinstance(self.assets, str):
            assets = [self.assets]

        for asset in assets:
            asset_path = self._mk_app_path(asset)
            remote_path = self.remote_assets / asset_path.relative
            self.host.push(asset_path.absolute, remote_path)
