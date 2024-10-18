=========
Changelog
=========

.. towncrier release notes start

0.2.2 (2024-10-18)
------------------

Fixed
~~~~~

- Dropped dependency pinning to allow installation with Python >3.10 (`#1 <https://github.com/lkubb/dooti/issues/1>`__)


0.2.1 (2022-11-09)
------------------

* Continue state application when app is absent
* Try to workaround a crash caused by exiting too early


0.2.0 (2022-11-09)
------------------

* Support idempotent state application from YAML config (dotfiles)
* BREAKING: rename class ``dooti.dooti`` to ``dooti.Dooti``


0.1.1 (2022-11-07)
------------------

* BREAKING: Introduce proper CLI interface.
* Allow multiple targets
* Add output formatting selection
* Add confirmation before apply
* Only apply necessary changes


0.0.1 (2022-01-28)
------------------

* First release.
