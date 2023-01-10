===============
Defining a host
===============

A manifest can define one host. A manifest which defines a host cannot be used in
``extends``.

A host definition has the following attributes:

``name``
  The IP or hostname of the server.

``port``
  The SSH port on the server.

  Default: ``22``

``user``
  Username for login

``home``
  Home dir for user

  Default: ``/home/{user}/``, where ``{user}``  is replaced by the username defined in
  the ``user`` attribute.

``root_path``
  Path to docker0s working dir on the server

  Should be absolute or relative to the connecting user's home directory, but do not use
  tildes.

``compose_command``
  Docker compose command.

  Default: ``docker-compose``



Example YAML:

.. code-block:: yaml

    host:
      name: example.com
      port: 2222
      user: example
      root_path: /var/docker0s
      compose_command: "docker compose"
