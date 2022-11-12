=====
Usage
=====

Commands
========

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

``docker0s cmd <app> <command> [<args> ...]``
  Execute a local App command

Options:

``--manifest=<file>``, ``-m <file>``:
  Specify the manifest. If not specified, it tries ``d0s-manifest.py`` then
  ``d0s-manifest.yml`` in the current directory.


Deployment
==========

Docker0s will deploy projects to your host using the following directory structure::

    /home/user/
      apps/
        app_name/
          service_name/
            docker-compose.yml
            env
        mounted_app_with_store/
          service_name/
            repo/
              docker-compose.yml
            store/
            env