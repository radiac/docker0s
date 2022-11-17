============
Writing apps
============

App types
=========

``docker0s.apps.App``
---------------------

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

  Default: ``app://d0s-manifest.py``, then ``app://d0s-manifest.yml`` (first found)

``compose``
  Path to the app's docker compose file.

  This can be a ``.yml`` file, or a ``.jinja2`` template. See "Compose templates" below
  for more details of template rendering.

  Default: ``app://docker-compose.jinja2``, then ``app://docker-compose.yml`` (first
  found)

``assets``:
  Path or list of paths to assets which should be uploaded into an ``assets`` dir next
  to the docker-compose. Must be ``app://`` paths.

``env_file``
  Path or list of paths to files containing environment variables for docker-compose.
  See "Environment variables" below for details.

``env``
  Key-value pairs of environment variables for docker-compose.
  See "Environment variables" below for details.

``compose_context``
  Key-value pairs of template variables to render a Jinja2 ``compose`` template.
  See "Compose templates" below for details.

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



``docker0s.apps.MountedApp``
----------------------------

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


Paths
=====

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

Environment variables can be used in your ``docker-compose.yml`` as normal, for example::

      services:
        my_service:
          environment:
            domain: "${hostname}"


Compose templates
=================

If the docker-compose file ends in a ``.jinja2`` extension, docker0s will treat it as a
Jinja2 template. See the `Jinja documentation <https://palletsprojects.com/p/jinja/>`_
for details of the template syntax.

The template will be able to reference other documents relative to it, regardless of
whether it is a local file or a remote file on a ``git+...`` url.

The template is rendered with the context dict provided in ``compose_context``, plus the
following values:

``host``
  A reference to the instantiated Host object.

  Example usage in a template::

      services:
        my_service:
          environment:
            domain: {{ host.name }}

``env``
  A reference to the fully resolved environment variables that will be sent to the
  server. It is recommended  to prefer environment variable substitution (eg
  ``${env_var}``) as it allows more flexibility when working on the server in the
  future, but the ``env`` context variable can be useful for conditional statements.

  Example usage in a template::

      services:
        my_service:
          environment:
            {% if env.domain %}
            domain: ${domain}
            {% endif %}

``apps``
  A reference to the compose template contexts of other apps in the current manifest.
  Note that this includes ``env`` and the other context variables mentioned here.

  Example usage in a template::

      services:
        my_service:
          {% if smtp_relay in apps %}
          networks:
            - {{ apps.smtp_relay.network }}
          {% endif %}

``docker0s``, ``globals``
  Reserved for future use.

Take care not to use these variables in your ``compose_context``.
