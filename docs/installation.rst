============
Installation
============

Local
=====

Using Python 3.10 or later, install using ``pip`` or ``pipx``::

    pip install docker0s


The local machine will need

* ``git`` (optional) - required for git-based paths


Manifest repository
-------------------

For most projects we recommend the following structure to keep your app and host
manifests separate to aid reusability:

::

    manifests/
      apps/
        app_name/
          docker-compose.yml
          d0s-manifest.yml
      hosts/
        host_name/
          d0s-manifest.yml

You do not have to follow this structure, and if you are just deploying off-the-shelf
app manifests then you can configure it all from a single manifest file if you would
prefer.

Host preparation
================

The host will need:

* ``docker`` and ``docker-compose`` (or podman equivalent)
* ``git`` (optional) - required for ``MountedApp`` apps
* a user to deploy the apps under
* appropriate firewall and security measures in place
