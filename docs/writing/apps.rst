============
Writing apps
============

App types
=========

``docker0s.apps.App``
---------------------

A project with a docker-compose ready for use in production.

Unless otherwise specified, all paths are relative to the manifest where they are
defined.

Attributes:

``extends``
  Path to a base docker0s manifest for this app.

  A base manifest:

  * uses the same syntax
  * can define multiple apps
  * can reference further base manifests
  * must not define a host

  A path can be a relative (to the current manifest) or absolute path:

  * ``path/to/d0s-manifest.yml``
  * ``/path/to/dir/containing/a/manifest/``

  It will look for an app with the same name by default; you can specify a different
  name with ``::<name>``, eg:

  * ``path/to/d0s-manifest.yml::AppName``

  It can also be a git URL in the format ``git+ssh://host:repo@commit#path::name``, or
  ``git+https://host/repo@commit#path::name``, where commit, path and name are optional, eg:

  * ``git+ssh://git@github.com:radiac/docker0s-manifests@main#traefik``
  * ``git+https://github.com/radiac/docker0s-manifests@v1.0#traefik/d0s-manifest.yml``
  * ``git+ssh://git@github.com:radiac/example.com``

  For security, when using a remote manifest from a third party git repository, we
  recommend performing a full audit of what you are going to deploy, and then pinning to
  that specific commit.

  Default: ``d0s-manifest.py``, then ``d0s-manifest.yml`` (first found)

``compose``
  Path to the app's docker compose file.

  This can be a YAML file (``.yml``, ``.yaml``), or a Jinja2 template (``.j2``,
  ``.jinja2``). See "Compose templates" below for more details of template rendering.

  Default: tries the following in order, uses first found: ``docker-compose.j2``,
  ``docker-compose.jinja2``, ``docker-compose.yml``, ``docker-compose.yaml``

``assets``:
  Path or list of paths to assets which should be uploaded into an ``assets`` dir next
  to the docker-compose.

``env_file``
  Path or list of paths to files containing environment variables for docker-compose.
  See :ref:`Environment variables <app_env>` below for details.

``env``
  Key-value pairs of environment variables for docker-compose.
  See :ref:`Environment variables <app_env>` below for details.

``compose_context``
  Key-value pairs of template variables to render a Jinja2 ``compose`` template.
  See :ref:`Compose templates <compose_templates>`_ for details.

Example YAML:

.. code-block:: yaml

    apps:
      website:
        extends: "git+ssh://git@github.com:radiac/example.com.git"
        compose: "docker-compose.live.yml"
        env_file:
        - base.env
        - website.env
        env:
          deployment=www.example.com


``docker0s.apps.RepoApp``
-------------------------

A project which requires the repository to be cloned on the host and mounted into
the service.

Takes the same arguments as an ``App``, with the following differences:

``repo``
  A ``git+`` URL to the repository and branch/commit to deploy to the server.

``repo_compose``
  Relative path to the compose file within the repository.

  If this path exists in the repo, Docker0s will overwrite it on the server.


Recommended configuration:

#. In the root of your repository, create a ``docker-compose.yml`` or
   ``docker-compose.j2``
#. Still in the root, create an app manifest - ``d0s-manifest.yml`` or
   ``d0s-manifest.py``
#. Add ``docker-compose.docker0s.yml`` to your ``.gitignore``

The ``RepoApp.compose`` will default to find the ``docker-compose.yml`` or ``.j2`` file,
and will write the production compose to ``docker-compose.docker0s.yml`` so that any
relative paths in the compose file will still resolve.

If you place the manifest or compose at a different location, you will need to set
``compose`` and ``repo_compose`` accordingly.

Example YAML:

.. code-block:: yaml

    apps:
      website:
        type: RepoApp
        repo: "git+ssh://git@github.com:radiac/example.com.git@main"
        compose: docker/docker-compose.live.j2
        repo_compose: docker/docker-compose.live.yml


.. _app_naming:

App naming
==========

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


.. _app_env:

Environment variables
=====================

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

Environment variables can be used in your ``docker-compose.yml`` as normal, for example:

.. code-block:: yaml

    services:
      my_service:
        environment:
          domain: "${hostname}"

Docker0s provides some environment variables by default - for more information see
:ref:`compose_env`.