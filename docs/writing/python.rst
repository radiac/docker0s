================
Python manifests
================

.. code-block:: python

    from docker0s import RepoApp

    class Website(RepoApp):
        # Clone a repo to the host and look for docker-compose.yml in there
        path = "git+ssh://git@github.com:radiac/example.com.git@main"
        env = {
            "DOMAIN": "example.radiac.net"
        }

        # Subclass operation methods to add your own logic
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



App commands
------------

Python App definitions can declare local commands - usually either utility functions to
assist with manifest definition, such as a password encoder, or to use fabric to perform
operations on the host, such as tailing docker logs.

To define an app, decorate it with ``App.command``:

.. code-block:: python

    class Website(App):
        @App.command
        def say_hello(self, name):
            print(f"Hello {name}, this runs locally")
            self.host.exec("echo And {name}, this is on the host", args={'name': name})


This can then be called as:

.. code-block:: bash

    ./docker0s cmd website say_hello person

Commands currently do not have any support for validation or typing of arguments.
