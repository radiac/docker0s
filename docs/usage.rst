=====
Usage
=====

Commands
========

Docker0s installs as ``docker0s`` and ``d0s`` for short

``docker0s ls``
  List the available apps

``docker0s deploy [<app>[.<service>]]``:
  Deploy resources to the host

``docker0s up [<app>[.<service>]]``:
  Start all apps, a specific app, or a specific app's service

``docker0s down [<app>[.<service>]]``:
  Stop all apps, a specific app, or a specific app's service

``docker0s restart [<app>[.<service>]]``:
  Restart all apps, a specific app, or a specific app's service

``docker0s exec <app>.<service> <command>``:
  Execute a command in the specific service

``docker0s status``
  Show the status of the containers on the host

``docker0s logs <app>.<service>``:
  Show host logs for the specified service

``docker0s cmd <app> <command> [<args> ...]``
  Execute a local App command

``docker0s use [<manifest|alias>] [--alias=<alias>]``
  Set or unset the default host manifest by either path or an alias.

``docker0s use --list``
  List aliases.


Options:

``--manifest=<file>``, ``-m <file>``:
  Specify the manifest for this command. Overrides the default manifest.


Specifying the manifest
-----------------------

The host manifest can be set using ``d0s use`` - for example::

    # Use foo.yml in the current dir and create an alias
    d0s use foo.yml --alias=foo

    # Swap tp to bar.yml
    d0s use bar.yml

    # Swap back to foo using the alias
    d0s use foo

    # Stop using a default
    d0s use

    # Clear the foo alias
    d0s use --alias=foo

This is saved to the docker0s user config, so will take effect across all active shell
sessions, and will persist across sessions and reboots. In this way it is somewhat
similar to ``kubectl config use-context``.

The config stores full paths, so aliases can be used to jump between manifests without
needing to specify the full path.

The manifest can also be set for each command with the ``--manifest`` option::

    $ d0s --manifest=baz.yml ls

If no manifest is specified, docker0s looks in the current directory for
``d0s-manifest.py`` then ``d0s-manifest.yml``.


Deployment
==========

Docker0s will deploy projects to your host using the following directory structure::

    /home/user/
      apps/
        app_name/
          store/
          docker-compose.yml
          env
        repo_app_with_store/
          repo/
            docker-compose.docker0s.yml
          store/
          env


Security considerations
=======================

You must always trust your manifest sources - remember that manifests can be arbitrary
Python code which is executed locally, and it has full shell access to your host.

For this reason we recommend you perform a full audit of any third-party manifests to
understand exactly what they are doing, and that if you extend manifests using ``git+``
URLs that you pin them to a specific commit.
