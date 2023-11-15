=========
Changelog
=========

Changes
=======

3.0.0 -
------------------

Features:

* Add progress reporting, logging, and report pretty-printing
* Add threads for parallel manifest loading
* Opt-in cache persistence across calls with new settings, see docs
* Add ``cache`` command to manage cache
* Add ``ls -l`` command option to show app inheritance
* Merge config and settings - some env vars have been renamed, see upgrade notes
* Merge ``compose_context`` from base apps so that newest key wins, rather than
  overwriting all keys.


Upgrading
~~~~~~~~~

#.  The following environment variables have been removed:

    * ``DOCKER0S_PATH`` is now removed
    * ``DOCKER0S_ENV_FILENAME``
    * ``DOCKER0S_COMPOSE_FILENAME``
    * ``DOCKER0S_DIR_ASSETS``

    A saved config file will automatically migrate to the new variables.

#. The cache dir has been moved; you can delete the ``~/.docker0s`` dir and its
   contents. We now use platformdirs to determine the correct place to store the
   cache (on linux that's ``~/.cache/docker0s``)



2.0.0 - 2022-01-10
------------------

Features:

* Simplify path specification so everything is relative to the originating manifest
* Rename ``MountedApp`` to ``RepoApp``, add ``repo`` and ``repo_compose`` arguments
* Add ``d0s`` command alias
* Add ``d0s use`` to set a default manifest
* Add ``d0s status`` and ``d0s log`` to assist host management

Bugfix:

* Fix inherited path resolution to be relative to the originating manifest's path
* Fix ``d0s exec``


1.2.0 - 2022-11-17
------------------

Features:

* Add Jinja2 template support for docker-compose.yml generation


1.1.0 - 2022-11-08
------------------

Features:

* Add command support - ``docker0s cmd ...``
* Restore default ``extends``
* Standardise manifest filenames


1.0.1 - 2022-10-31
------------------

Bugfix:

* Fix for entrypoint


1.0.0 - 2022-10-31
------------------

Initial release



Roadmap
=======

* Git hash pinning for improved security
* Support for gitops through a repository monitoring mode

