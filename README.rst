========
docker0s
========

Docker0s uses docker-compose to manage multiple containerised apps on a single host.

.. image:: https://img.shields.io/pypi/v/docker0s.svg
    :target: https://pypi.org/project/docker0s/
    :alt: PyPI

.. image:: https://github.com/radiac/docker0s/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/docker0s/actions/workflows/ci.yml
    :alt: Tests

.. image:: https://codecov.io/gh/radiac/docker0s/branch/main/graph/badge.svg?token=BCNM45T6GI
    :target: https://codecov.io/gh/radiac/docker0s
    :alt: Test coverage


Bring together standard docker-compose files across multiple projects in a single simple
manifest file, written in either YAML or Python with pre- and post-operation hooks, to
deploy to a single host.

It's designed for small self-hosted low-maintenance deployments which don't need the
complexity of Kubernetes - think k8s with zero features and a much simpler config
syntax, with simple app manifests instead of helm charts.

There is a collection of ready-to-use app manifests at `docker0s-manifests`_, with
examples for how to deploy them to your host.

.. _docker0s-manifests: https://github.com/radiac/docker0s-manifests


Quickstart
==========

Install::

    pip install docker0s


Put together a manifest in YAML as ``d0s-manifest.yml``:

.. code-block:: yaml

    apps:
      traefik:
        path: git+https://github.com/radiac/docker0s-manifests.git@main#traefik
        env_file: traefik.env
      mail:
        path: ../apps/mail
      website:
        type: MountedApp
        path: "git+ssh://git@github.com:radiac/example.com.git@main"
        env:
          DOMAIN: example.radiac.net
    host:
      name: example.radiac.net


or in Python as ``d0s-manifest.py``, using subclassing to perform actions before and
after operations, and to add custom functionality:

.. code-block:: python

    from docker0s import MountedApp

    class Website(MountedApp):
        # Clone a repo to the host and look for docker-compose.yml in there
        path = "git+ssh://git@github.com:radiac/example.com.git@main"
        env = {
            "DOMAIN": "example.radiac.net"
        }

        # Subclass methods to add your own logic
        def deploy(self):
            # Perform action before deployment, eg clean up any previous deployment
            super().deploy()
            # Perform action after deployment, eg push additional resources

        def up(self, *services):
            # Perform action before ``up``, eg report to a log
            super().up(*services)
            # Perform action after ``up``, eg wait and perform a test

        @App.command
        def say_hello(self, name):
            print(f"Hello {name}, this runs locally")
            self.host.exec("echo And {name}, this is on the host", args={'name': name})

    class Vagrant(Host):
        name = "vagrant"


Then run a command, eg::

    docker0s deploy
    docker0s up
    docker0s restart website.django
    docker0s exec website.django /bin/bash
    docker0s cmd website say_hello person


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
  Specify the manifest. If not specified, tries ``d0s-manifest.py`` then
  ``d0s-manifest.yml`` in the current directory.


Manifest file
=============

A manifest file defines a list of more or apps which will be deployed to one host.

You can put everything in a single manifest, but usually you will define a generic *app
manifest* next to a docker-compose.yml, and then extend it in a *host manifest* where
you set environment variables. The syntax of both is the same, but an app manifest only
defines apps, whereas a host manifest defines both apps and the host to deploy it to.

See `docker0s-manifests <https://github.com/radiac/docker0s-manifests>`_ for a
collection of app manifests and examples for how to use them with your host manifest.


YAML
----

A manifest file has two sections:

``apps``:
  The list of app definitions.

  Each app starts with its identifier. This is used as its namespace for
  docker-compose.

  Under the identifier you can declare the type of app with ``type``; if not specified
  it will default to ``type: App``. See "App Types" for more details and additional
  arguments for the app definition.

  An app can also specify environment variables to pass to docker-compose, by setting
  ``env`` with a file path, a list of files, or key/value pairs.

``host``:
  The host definition.

  There can be only one per manifest. Manifests which define a host cannot be used as a
  base manifest (see ``extends`` attribute).


App types
---------

``App``:
  A project with a docker-compose ready for use in production.

  Attributes:

  ``path``
    Path to the app - a directory or repository containing the docker compose file and
    any other assets docker0s will require. Any ``app://`` paths elsewhere in the app
    definition will use this as the base path.

  ``extends``
    Path to a base docker0s manifest for this app.

    A base manifest:

    * uses the same syntax
    * can define multiple apps
    * can reference further base manifests
    * must not define a host

    This value can be one of two patterns:

    * ``path/to/d0s-manifest.yml`` or ``path/to/d0s-manifest.py`` - this app will extend
      using the app defined with the same name - see "App naming" below
    * ``path/to/d0s-manifest.yml::AppName`` or ``path/to/d0s-manifest.py::AppName`` -
      this app will extend using the app defined with the name ``AppName``.

    Default: ``app://d0s-manifest.py``, ``app://d0s-manifest.yml`` (first found)

  ``compose``
    Path to the app's docker compose file.

    Default: ``app://docker-compose.yml``

  ``assets``:
    Path or list of paths to assets which should be uploaded into an ``assets`` dir next
    to the docker-compose. Must be ``app://`` paths.

  ``env_file``
    Path or list of paths to files containing environment variables for docker-compose.
    See "Environment variables" below for details.

  ``env``
    Key-value pairs of environment variables for docker-compose.
    See "Environment variables" below for details.

  Example YAML:

  .. code-block:: yaml

      apps:
        website:
          path: "git+ssh://git@github.com:radiac/example.com.git"
          extends: "app://docker0s-base.py"
          config: "app://docker-compose.live.yml"
          env_file:
          - app://base.env
          - website.env
          env:
            deployment=www.example.com



``MountedApp``:
  A project which requires the repository to be cloned on the host and mounted into
  the service.

  Takes the same arguments as an ``App``, with the following differences:

  ``path``
    Path to the app. This must be a git repository.

  ``compose``
    Path to the app's docker compose file. This must be an ``app://`` path within the
    repository.

  Example YAML:

  .. code-block:: yaml

      apps:
        website:
          type: MountedApp
          path: "git+ssh://git@github.com:radiac/example.com.git"


App naming
----------

Because apps are referenced by name in Python, YAML and on the command line, docker0s
supports apps names in ``PascalCase``, ``camelCase``, ``snake_case`` and ``kebab-case``
in YAML and the command line. Python classes must always use ``PascalCase``:

.. code-block:: python

    class WebsiteExampleCom(App):
        path = "../website"

YAML can use any - these four app definitions are equivalent (so would raise an error):

.. code-block:: yaml

    apps:
      website_example_com:
        path: ../website
      website-example-com:
        path: ../website
      websiteExampleCom:
        path: ../website
      WebsiteExampleCom:
        path: ../website


Paths
-----

An App ``path`` can be:

* relative to the manifest, eg ``traefik.env`` or ``../apps/traefik/d0s-manifest.yml``.
  Note this is relative to the manifest where this app definition is found, so relative
  paths in a base manifest loaded with ``extend`` will be relative to the base manifest.
* absolute, eg ``/etc/docker0s/apps/traefik/d0s-manifest.yml``.
* a file in a git repository in the format ``git+<protocol>://<path>@<ref>#<file>``
  where protocol is one of ``git+https`` or ``git+ssh``, and the ref is a
  branch, commit or tag. For example:

  * ``git+ssh://git@github.com:radiac/docker0s-manifests@main#traefik``
  * ``git+https://github.com/radiac/docker0s-manifests@v1.0#traefik/d0s-manifest.yml``


Other fields which take a path argument (ie ``manifest``, ``compose`` and ``env_file``)
can use these values, as well as:

* relative to the app's path with ``app://``, eg if ``path = "../apps/traefik"``
  then if ``extends = "app://docker0s-base.py"`` it will look for the base manifest at
  ``../apps/traefik/docker0s-base.py``

For security, when using a remote manifest from a third party git repository, we
recommend performing a full audit of what you are going to deploy, and then pinning to
that specific commit.


Environment variables
---------------------

Environment variables for the docker-compose can be defined as one or more env files, as
a dict within the manifest, or both.

If more than one ``env_file`` is specified, files are loaded in order. If a key appears
in more than one file, the last value loaded will be used.

If a key appears in both the ``env`` dict and an ``env_file``, the value in this field
will be used.

Environment variables are evaluated before inheritance, meaning an env file key in a
child manifest can override an env dict key in a parent. Precedence order, with winner
first:

#. Child env dict
#. Child env file
#. Parent env dict
#. Parent env file

Environment variables are merged and written to an env file on the server for
docker-compose to use.


App commands
------------

Python App definitions can declare local commands - usually either utility functions to
assist with manifest definition, such as a password encoder, or to use fabric to perform
operations on the host, such as tailing docker logs.

To define an app, decorate it with ``App.command``::

    class Website(App):
        @App.command
        def say_hello(self, name):
            print(f"Hello {name}, this runs locally")
            self.host.exec("echo And {name}, this is on the host", args={'name': name})


This can then be called as:

    ./docker0s cmd website say_hello person

Commands currently do not have any support for validation or typing of arguments.


Deployment
==========

Default deployment structure::

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


Roadmap
=======

* Jinja support for templated docker compose files
* Base manifest hashes, for improved security when pulling remotely
* Support for gitops through a repository monitoring mode


Changelog
=========

* 1.1.0 - Add command support, ``docker0s cmd ...``; restore default ``extends``;
  standardise manifest filenames
* 1.0.1 - Fix for entrypoint
* 1.0.0 - Initial release
