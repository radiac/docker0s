========
docker0s
========

Docker0s uses docker-compose to manage multiple containerised apps on a single host.

.. image:: https://img.shields.io/pypi/v/docker0s.svg
    :target: https://pypi.org/project/docker0s/
    :alt: PyPI

.. image:: https://readthedocs.org/projects/docker0s/badge/?version=latest
    :target: https://docker0s.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

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


* Project site: https://radiac.net/projects/docker0s/
* Documentation: https://docker0s.readthedocs.io/
* Source code: https://github.com/radiac/docker0s



Quickstart
==========

Install::

    pip install docker0s


Put together a manifest in YAML as ``d0s-manifest.yml``:

.. code-block:: yaml

    apps:
      traefik:
        extends: git+https://github.com/radiac/docker0s-manifests.git#traefik
        env_file: traefik.env
      smtp:
        compose: smtp.yml
      website:
        type: RepoApp
        extends: "git+ssh://git@github.com:radiac/example.com.git@main"
        env:
          DOMAIN: docker0s.example.com
    host:
      name: docker0s.example.com

See `writing manifests`_ for a full reference

.. _writing manifests: https://docker0s.readthedocs.io/en/latest/writing/index.html


Then deploy your code and bring up the containers::

    d0s deploy
    d0s up

You can then use docker0s to manage your deployment::

    # Restart a container
    d0s restart website.django

    # Run a command inside a container
    d0s exec website.django /bin/bash

See `commands`_ for a full command reference

.. _commands: https://docker0s.readthedocs.io/en/latest/usage.html


Python power
============

You can also write your manifests in Python as ``d0s-manifest.py``, using subclassing to
perform actions before and after operations, and to extend docker0s with custom
commands:

.. code-block:: python

    from docker0s import RepoApp

    class Website(RepoApp):
        # Clone a repo to the host and look for docker-compose.yml in there
        extends = "git+ssh://git@github.com:radiac/example.com.git@main"
        env = {
            "DOMAIN": "docker0s.example.com"
        }

        # Subclass operation methods to add your own logic
        def deploy(self):
            # Perform action before deployment, eg clean up any previous deployment
            super().deploy()
            # Perform action after deployment, eg push additional resources

        @App.command
        def say_hello(self, name):
            print(f"Hello {name}, this runs locally")
            self.host.exec("echo And {name}, this is on the host", args={'name': name})

    class MyServer(Host):
        name = "myserver.example.com"

The command is then available as::

    d0s website:hello
