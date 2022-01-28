=====
Usage
=====

As a python module
------------------
To use dooti in a project::

    import dooti
    d = dooti.dooti()

    # set default handler for csv files
    # the extension has to be registered with MacOS and
    # the handler has to be installed
    d.set_default_ext("csv", "Sublime Text")

    # get default handler for http scheme
    handler = d.get_default_scheme("http")



As a CLI utility
----------------
Show file path to current handler of file extension::

    dooti ext csv

Show file path to current handler of URL scheme::

    dooti scheme http

Set default handler for file extension::

    dooti ext csv "Sublime Text"
    dooti ext csv com.sublimetext.4
    dooti ext csv "/Applications/Sublime Text.app"

Set default handler for URL scheme::

    dooti scheme http Firefox
    dooti scheme http org.mozilla.firefox
    dooti scheme http /Applications/Firefox.app
