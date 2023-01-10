=================
Writing manifests
=================

A manifest file defines a list of more or apps which will be deployed to one host.

You can put everything in a single manifest, but usually you will define a generic *app
manifest* next to a ``docker-compose.yml``, and then extend it in a *host manifest*
where you set environment variables specific to your host. The syntax of both is the
same, but an app manifest only defines apps, whereas a host manifest defines both apps
and the host to deploy it to.

See `docker0s-manifests <https://github.com/radiac/docker0s-manifests>`_ for a
collection of app manifests and examples for how to use them with your host manifest.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   yaml
   python
   apps
   host
   compose
