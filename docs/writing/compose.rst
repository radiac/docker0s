====================
Docker compose files
====================

.. _compose_env:

Environment variables
=====================

You can pass your own environment variables into your docker-compose file - for more
details see :ref:`app_env`.

A standard docker0s app provides the following environment variables:

``ENV_FILE``
  Path to the combined env file on the host

``ASSETS_PATH``
  Path to the assets dir on the host

  Assets are resources pushed to the server as part of the docker0s deployment - config
  files, scripts, media etc.

``STORE_PATH``
  Path to the store dir on the host

  The store is for files created by the containers - logs, databases, uploads etc.


Example usage in your ``docker-compose.yml``:

.. code-block:: yaml

  services:
    postgres:
      image: postgres:latest
      restart: unless-stopped
      env_file: "${ENV_FILE}"
      volumes:
        - "${STORE_PATH}/db:/db"
        - "${ASSET_PATH}/scripts:/scripts"


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

  Example usage in a template:

  .. code-block:: yaml

      services:
        my_service:
          environment:
            domain: {{ host.name }}


``env``
  A reference to the fully resolved environment variables that will be sent to the
  server. It is recommended  to prefer environment variable substitution (eg
  ``${env_var}``) as it allows more flexibility when working on the server in the
  future, but the ``env`` context variable can be useful for conditional statements.

  Example usage in a template:

  .. code-block:: yaml

      services:
        my_service:
          environment:
            {% if env.domain %}
            domain: ${domain}
            {% endif %}


``apps``
  A reference to the compose template contexts of other apps in the current manifest.
  Note that this includes ``env`` and the other context variables mentioned here.

  App names are normalised, so can be specified as described in :ref:`app_naming`, eg
  ``apps.MyApp``, ``apps.my_app`` etc

  Example usage in a template:

  .. code-block:: yaml

      services:
        my_service:
          {% if smtp_relay in apps %}
          networks:
            - {{ apps.smtp_relay.network }}
          {% endif %}


``docker0s``, ``globals``
  Reserved for future use.

Take care not to use these variables in your own ``compose_context``.
