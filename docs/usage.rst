=====
Usage
=====

CLI
---
::

    usage: dooti [-h] [-f {json,yaml}] [-y] [-t] {apply,ext,scheme,uti} ...

    Manage default handlers on macOS.

    positional arguments:
      {apply,ext,scheme,uti}
                            commands
        apply               Apply a YAML state configuration.
        ext                 Manage the default handler for all UTI associated with file extensions
        scheme              Manage default handler for URI scheme(s)
        uti                 Manage default handler for UTI(s)

    options:
      -h, --help            show this help message and exit
      -f {json,yaml}, --format {json,yaml}
                            The output format. Defaults to YAML.
      -y, --yes             Do not ask for consent, assume yes.
      -t, --dry-run         Only show planned changes and exit.

Configuration
~~~~~~~~~~~~~
``dooti`` can also ensure the state of handler associations on your system via a YAML configuration file (by running ``dooti apply``). If you do not provide an explicit path, ``dooti`` will look in the following locations and load the first found file:

* ``$XDG_CONFIG_HOME/dooti.yaml``
* ``$XDG_CONFIG_HOME/dooti.yml``
* ``$XDG_CONFIG_HOME/dooti/dooti.yaml``
* ``$XDG_CONFIG_HOME/dooti/dooti.yml``
* ``$XDG_CONFIG_HOME/dooti/config.yaml``
* ``$XDG_CONFIG_HOME/dooti/config.yml``

The expected configuration format is as follows:

.. code-block:: yaml

    # All handlers in this file can be specified as usual,
    # meaning name, bundle ID or absolute path.

    # Manage file extension associations.
    ext:
      nfo: Notes
      jpeg: Preview

    # Manage URI scheme associations.
    scheme:
      http: Firefox
      mailto: Mail

    # Manage specific UTI associations.
    uti:
      public.c‑source: Sublime Text

    # Manage associations per app/handler.
    app:
      Sublime Text:
        ext:
          - py
          - rst
          - yml
          - yaml
        uti:
          - public.fortran‑source

      Brave Browser:
        scheme:
          - ipfs


Examples
~~~~~~~~
Show file path(s) to current handler(s) of file extension(s)::

    dooti ext csv

Show file path(s) to current handler(s) of URI scheme(s)::

    dooti scheme http https

Set default handler for file extension(s)::

    dooti ext csv -x "Sublime Text"
    dooti ext csv -x com.sublimetext.4
    dooti ext csv -x "/Applications/Sublime Text.app"

Set default handler for URI scheme(s)::

    dooti scheme http -x Firefox
    dooti scheme http -x org.mozilla.firefox
    dooti scheme http -x /Applications/Firefox.app

Show proposed changes from explict config file::

    dooti -t apply -i my_conf.yaml

Automatically apply idempotent state from dotfiles and show output using ``jq``::

    dooti -yf json apply | jq


As a python module
------------------
To use dooti in a project::

    import dooti
    d = dooti.Dooti()

    # set default handler for csv files
    # the extension has to be registered with MacOS and
    # the handler has to be installed
    d.set_default_ext("csv", "Sublime Text")

    # get default handler for http scheme
    handler = d.get_default_scheme("http")
