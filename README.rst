========
docker0s
========

Overview
========

Docker0s uses docker-compose to manage multiple containerised apps on a single machine.

Bring together standard docker-compose files across multiple projects in a single simple
manifest file, written in either YAML or Python with pre- and post-deployment hooks, to
deploy to a single host.

It's designed for small self-hosted low-maintenance deployments which don't need the
complexity of Kubernetes - think k8s with zero features and a much simpler config
syntax.


Quickstart
==========

Install::

    pip install docker0s


Put together a manifest in Python as ``manifest.py``:

.. code-block:: python

    from docker0s import App, MountedApp, Host

    class Traefik(App):
       # Use local docker-compose and env files
        path = "../../apps/traefik"
        compose = "app://docker-compose.prod.yml"
        env_file = "traefik.env"

    class Website(MountedApp):
        # Clone a repo to the host and look for docker-compose.yml in there
        path = "git+ssh://git@github.com:radiac/example.com.git@main"
        env = {
            "DOMAIN": "example.radiac.net"
        }

        def post_deploy(self, host: Host):
            # Perform action after deployment, mixins available

    class Vagrant(Host):
        name = "vagrant"
        secrets = "host.env"


or in YAML as ``manifest.yml``:

.. code-block:: yaml

    apps:
      traefik:
        path: ../../apps/traefik
        env_file: traefik.env
      website:
        type: MountedApp
        path: "git+ssh://git@github.com:radiac/example.com.git@main"
        env:
          DOMAIN: example.radiac.net
    host:
      name: example.radiac.net


Then run a command:


For example::

    docker0s deploy
    docker0s up
    docker0s restart website.django
    docker0s exec website.django /bin/bash


Commands
========

``docker0s deploy``:
  Deploy resources to the host

``docker0s up [<app>[.<service>]]``:
  Start all apps, a specific app, or a specific app's service

``docker0s down [<app>[.<service>]]``:
  Stop all apps, a specific app, or a specific app's service

``docker0s restart [<app>[.<service>]]``:
  Restart all apps, a specific app, or a specific app's service

``docker0s exec <app>.<service> command``:
  Execute a command in the specific service


Options:

``--manifest=<file>``, ``-m <file>``:
  Specify the manifest. If not specified, tries ``manifest.py`` then ``manifest.yml`` in
  the current directory.


Manifest file
=============

A manifest file defines a list of more or apps which will be deployed to one host.

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

  There can be only one per manifest.


App types
---------

``App``:
  A project with a docker-compose ready for use in production.

  Arguments:

  ``path``
    Path to the app. Any ``app://`` paths elsewhere in the app definition will use this
    as the base path.

  ``extends``
    Path to a base docker0s manifest for this app.

    A base manifest:

    * uses the same syntax
    * must define an app with the same name as the one extending it - see "App naming"
      below
    * can define multiple apps
    * must not define a host

    Default: ``app://docker0s.py``, then ``app://docker0s.yml``

  ``compose``
    Path to the app's docker compose file.

    Default: ``app://docker-compose.yml``

  ``env_file``
    Path or list of paths to files containing environment variables for docker-compose.

    If more than one file is specified, files are loaded in order. If a key appears in
    more than one file, the last value loaded will be used.

  ``env``
    Key-value pairs of environment variables for docker-compose. If used with
    ``env_file``, if a key appears in both the value in this field will be used.

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
    Path to the app. If this is a git repository it will be cloned to the remote host,
    otherwise it will be pushed from a local path.

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
in YAML and the command line.

Python classes must use ``PascalCase``:

.. code-block:: python

    class WebsiteExampleCom(App):
        path = "../website"

YAML can use any - these four app definitions are equivalent (so would raise an error)::

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

* relative to the manifest, eg ``traefik.env`` or ``../../apps/traefik/manifest.yml``.
  Note this is relative to the manifest where this app definition is found, so relative
  paths in a base manifest loaded with ``extend`` will be relative to the base manifest.
* absolute, eg ``/etc/docker0s/apps/traefik/manifest.yml``.
* a file in a git repository in the format ``git+<protocol>://<path>@<ref>#<file>``
  where protocol is one of ``git+https`` or ``git+ssh``, and the ref is a
  branch, commit or tag. For example:

  * ``git+ssh://git@github.com:radiac/docker0s@main#apps/traefik/manifest.yml``
  * ``git+https://github.com/radiac/docker0s@v1.0#apps/traefik/manifest.yml``


Other fields which take a path argument (ie ``manifest``, ``compose`` and ``env_file``)
can use these values, as well as:

* relative to the app's path with ``app://``, eg if ``path = "../../apps/traefik"``
  then if ``extends = "app://docker0s.py"`` it will look for the base manifest at
  ``../../apps/traefik/docker0s.py``
