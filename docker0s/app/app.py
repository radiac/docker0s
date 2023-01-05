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
        self.push_assets_to_host()

    def push_assets_to_host(self):
        cls_assets = self.collect_attr("assets")
        files: str | list[str]
        for mro_cls, files in cls_assets:
            if not files:
                continue

            if isinstance(files, str):
                files = [files]

            for file in files:
                asset_path = mro_cls._dir / file
                remote_path = self.remote_assets / file
                self.host.push(asset_path, remote_path)
