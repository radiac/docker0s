=========
Changelog
=========

Changes
=======

2.0.0 -
------------------

Features:

* Simplify path specification so everything is relative to the originating manifest
* Fix inherited path resolution to be relative to the originating manifest's path
* Rename ``MountedApp`` to ``RepoApp``, add ``repo`` and ``repo_compose`` arguments
* Add ``d0s`` command alias
* Add ``d0s use`` to set a default manifest
* Add ``d0s status`` and ``d0s log`` to assist host management


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

* Fix for entrypoint

1.0.0 - 2022-10-31
------------------

* 1.0.0 - Initial release



Roadmap
=======

* Git hash pinning for improved security
* Support for gitops through a repository monitoring mode

