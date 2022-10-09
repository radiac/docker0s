from __future__ import annotations

from io import StringIO
from pathlib import Path, PosixPath
from shlex import quote
from typing import Any

from fabric import Connection
from fabric.runners import Result

from .manifest_object import ManifestObject


class Host(ManifestObject, abstract=True):
    #: Abstract base classes should be marked as abstract so they are ignored by the
    #: manifest loader
    abstract: bool = True

    #: Server hostname
    name: str

    #: Server port
    port: str | int | None

    #: Username for login
    user: str | None

    #: Path to the docker0s working dir on the server
    #:
    #: Should be absolute or relative to the connecting user's home directory, do not
    #: use tildes. See fabric docs for details:
    #: https://docs.fabfile.org/en/stable/api/transfer.html
    root_path: str = "apps"

    # Internal connection handle
    _connection: Connection | None = None

    def __str__(self) -> str:
        value = self.name
        if self.port:
            value = f"{value}:{self.port}"
        if self.user:
            value = f"{self.user}@{value}"
        return value

    def path(self, app, service: str | None = None) -> PosixPath:
        """
        Remote path builder to ensure consistency
        """
        path = PosixPath(self.root_path) / app
        if service:
            path /= service
        return path

    @property
    def connection(self) -> Connection:
        """
        Create an SSH connection, or retrieve an existing one
        """
        if not self._connection:
            self._connection = Connection(
                host=self.name,
                port=self.port,
                user=self.user,
            )
        return self._connection

    def exec(
        self,
        cmd: str,
        args: dict[str, Any] | None = None,
        env: dict[str, Any] | None = None,
    ) -> Result:
        """
        Execute a command on the remote server

        Args:
            cmd (str): The command string to execute on the server. Can use named
                placeholders for use with ``.format`` and the ``args`` dict
            args (dict |None): Optional dict of command arguments. These will be escaped
                and passed into cmd.format().
            env (dict | None): Optional dictionary of env vars to run the command with.
                Note that this is an independent dict which will not use App env
                definitions unless you pass env=App.get_env_data()
        """
        if args is not None:
            safe_args = {key: quote(str(val)) for key, val in args.items()}
            cmd = cmd.format(**safe_args)
        result: Result = self.connection.run(cmd, env=env)
        if not result.ok:
            raise ValueError(f"Command '{cmd}' failed: {result.stderr.strip()}")
        return result

    def call_compose(
        self,
        compose: PosixPath,
        env: PosixPath,
        cmd: str,
        cmd_args: dict[str, Any] | None = None,
    ):
        """
        Execute a docker-compose command on the server

        The paths for compose and env are wrapped in quotes, the command is passed to
        the host unaltered
        """
        args = {"compose": compose, "env": env}
        if cmd_args:
            args.update(cmd_args)
        self.exec(
            cmd=f"docker-compose --file {{compose}} --env-file {{env}} {cmd}",
            args=args,
        )

    def push(self, source: Path, destination: PosixPath):
        """
        Push a file to the server
        """
        self.ensure_parent_path(destination)
        self.connection.put(str(source), str(destination))

    def write(self, filename: PosixPath, content: str):
        """
        Write a file to the server
        """
        self.ensure_parent_path(filename)
        data = StringIO(content)
        self.connection.put(data, str(filename))

    def ensure_parent_path(self, filename: PosixPath):
        """
        Given a path to a file, ensure the parent directory exists.

        For example::

            host.ensure_parent_path(root / "app_name" / "env")

        will connect to the server and run::

            mkdir -p "{root}/app_name"
        """
        self.mkdir(filename.parent)

    def mkdir(self, path: PosixPath):
        """
        Make the specified dir and any parent dirs on the host

        If it already exists, fail silently
        """
        self.exec("mkdir -p {path}", args={"path": path})
