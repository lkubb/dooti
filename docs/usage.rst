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
Show file path(s) to current handler(s) of file extension(s)::

    dooti ext csv

Show file path(s) to current handler(s) of URL scheme(s)::

    dooti scheme http https

Set default handler for file extension(s)::

    dooti ext csv -x "Sublime Text"
    dooti ext csv -x com.sublimetext.4
    dooti ext csv -x "/Applications/Sublime Text.app"

Set default handler for URL scheme(s)::

    dooti scheme http -x Firefox
    dooti scheme http -x org.mozilla.firefox
    dooti scheme http -x /Applications/Firefox.app
