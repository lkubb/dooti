=====
dooti
=====

Set default handlers for files and URL schemes on MacOS 12.0+.

Why?
----
Most existing tools use `LSSetDefaultRoleHandlerForContentType <https://developer.apple.com/documentation/coreservices/1447588-lssethandleroptionsforcontenttyp?language=objc>`_ and `LSSetDefaultHandlerForURLScheme <https://developer.apple.com/documentation/coreservices/1447760-lssetdefaulthandlerforurlscheme?language=objc>`_, which are deprecated and apparently only available up to macOS 12.0. ``dooti`` uses a different API and should work on Monterey (12.0) and above.

Limitations
-----------
* This tool was built out of necessity for myself and is not battle-tested.
* The CLI interface is very spartan currently, including not being very talkative and not catching exceptions.
* The designated handler has to be installed before running the command for this to work at all.
* Setting some URL scheme handlers (especially for http) might cause a prompt.
* Setting some file extension handlers might be restricted (especially html seems to fail silently).

Installation
------------
I recommend installing with `pipx <https://pypa.github.io/pipx/>`_, although pip will work fine as well:

.. code-block:: bash

        pipx install dooti

Quickstart
----------
``dooti`` currently supports three commands:

ext
    specify handlers for file extensions (will be automapped to associated UTI)
scheme
    specify handlers for URL schemes
uti
    specify handlers for specific UTI

The first argument is always the target file extension / URL scheme / UTI. This allows you to inspect the current handlers for the specific target:

.. code-block:: console

    $ dooti ext html
    /Applications/Firefox.app
    $ dooti scheme http
    /Applications/Firefox.app
    $ dooti uti public.html
    /Applications/Firefox.app

When you want to change a setting, you need to specify the second argument, which is the default handler to set. The following three formats are supported:

* name of application:

    .. code-block:: bash

        dooti ext csv "Sublime Text"

* absolute filesystem path:

    .. code-block:: bash

        dooti scheme http "/Applications/Firefox.app"

* bundle ID

    .. code-block:: bash

        dooti uti py com.sublimetext.4


Similar tools
-------------
* `duti <https://github.com/moretension/duti>`_
* `openwith <https://github.com/jdek/openwith>`_
* `defaultbrowser <https://gist.github.com/miketaylr/5969656>`_
* `SwiftDefaultApps <https://github.com/Lord-Kamina/SwiftDefaultApps>`_
