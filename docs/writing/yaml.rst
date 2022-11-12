==============
YAML manifests
==============

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

