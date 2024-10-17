import argparse
import json
import logging
import sys
import time
from pathlib import Path

import yaml
from xdg import xdg_config_home

from .dooti import ApplicationNotFound, Dooti

log = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="{levelname}: {message}", style="{"
)


class DootiCLI:
    """
    Wraps Dooti for the command line.
    """

    changes = {}
    errors = []
    handlers = {}
    scopes = ("ext", "scheme", "uti")

    def __init__(self, assume_yes=False, dry_run=False, fmt="yaml"):
        self.do = Dooti()
        self.assume_yes = assume_yes
        self.dry_run = dry_run
        self.fmt = fmt

    def apply_(self, file=None, dynamic=False):
        """
        Apply configuration from a file.
        """
        file = self._find_config(file)
        definitions = self._load_config(file)

        parsed = {"extensions": {}, "schemes": {}, "utis": {}}

        for ext, handler in definitions.get("ext", {}).items():
            try:
                _, single = self.ext([ext], dynamic=dynamic, handler=handler)
                parsed["extensions"].update(single["extensions"])
            except ApplicationNotFound as err:
                self.errors.append(str(err))

        for scope in ("scheme", "uti"):
            parser = getattr(self, scope)
            for item, handler in definitions.get(scope, {}).items():
                try:
                    _, single = parser([item], handler=handler)
                    parsed[f"{scope}s"].update(single[f"{scope}s"])
                except ApplicationNotFound as err:
                    self.errors.append(str(err))

        for handler, app_config in definitions.get("app", {}).items():
            if "ext" in app_config:
                try:
                    _, single = self.ext(
                        app_config["ext"], dynamic=dynamic, handler=handler
                    )
                    parsed["extensions"].update(single["extensions"])
                except ApplicationNotFound as err:
                    self.errors.append(str(err))
            for scope in ("scheme", "uti"):
                if scope in app_config:
                    parser = getattr(self, scope)
                    try:
                        _, single = parser(app_config[scope], handler=handler)
                        parsed[f"{scope}s"].update(single[f"{scope}s"])
                    except ApplicationNotFound as err:
                        self.errors.append(str(err))

        return None, parsed

    def ext(self, extensions, dynamic=False, handler=None):
        """
        Set handler or get handlers for a list of file extensions.
        """
        current = {ext: self.do.get_default_ext(ext) for ext in extensions}
        if handler is None:
            return current, None

        handler = self._lookup_handler(handler)
        if not dynamic:
            allowed_extensions = [
                ext for ext in extensions if not self.do.is_dynamic_uti(ext)
            ]
            disallowed_extensions = set(extensions) - set(allowed_extensions)
            for ext in disallowed_extensions:
                self.errors.append(
                    f"No UTI are registered for file extension '{ext}'. "
                    "To force using a dynamic UTI, pass `-u`/`--dynamic`."
                )
            extensions = allowed_extensions

        diff = {
            ext: {"from": current[ext], "to": handler}
            for ext in extensions
            if current[ext] != handler
        }

        return current, {"extensions": diff}

    def scheme(self, schemes, handler=None):
        """
        Set handler or get handlers for a list of schemes.
        """
        current = {scheme: self.do.get_default_scheme(scheme) for scheme in schemes}

        if handler is None:
            return current, None

        handler = self._lookup_handler(handler)

        diff = {
            scheme: {"from": current[scheme], "to": handler}
            for scheme in schemes
            if current[scheme] != handler
        }

        return current, {"schemes": diff}

    def uti(self, utis, handler=None):
        """
        Set handler or get handlers for a list of UTI.
        """
        current = {uti: self.do.get_default_uti(uti) for uti in utis}

        if handler is None:
            return current, None

        handler = self._lookup_handler(handler)

        diff = {
            uti: {"from": current[uti], "to": handler}
            for uti in utis
            if current[uti] != handler
        }

        return current, {"utis": diff}

    def run(self, func, args):
        """
        Call the requested function, catch errors and handle output.
        """
        ret = None
        try:
            current, diff = getattr(self, func)(**vars(args))
            if diff is None:
                ret = current
            else:
                self._apply_diff(diff)
        except (ValueError, yaml.parser.ParserError, ApplicationNotFound) as err:
            self.errors.append(str(err))
        except Exception as err:  # pylint: disable=broad-except
            log.error(str(err))
        finally:
            self._output(ret)
            # bandaid for PyThread_exit_thread / pthread_exit being called too early
            # because pyobjc does not have the correct metadata for completionHandler
            if ret is None:
                time.sleep(0.1)
            sys.exit(int(bool(self.errors)))

    def _apply_diff(self, diff):
        if self.dry_run or not any(
            (scope in diff and diff[scope])
            for scope in ("extensions", "schemes", "utis")
        ):
            self.changes = diff
            return
        if not (self.assume_yes or self._ask_consent(diff)):
            log.info("Did not get consent to apply changes. Exiting.")
            return

        if "extensions" in diff:
            for ext, handler in diff["extensions"].items():
                self.do.set_default_ext(ext, handler["to"], allow_dynamic=True)
            self.changes["extensions"] = diff["extensions"]

        if "schemes" in diff:
            for scheme, handler in diff["schemes"].items():
                self.do.set_default_scheme(scheme, handler["to"])
            self.changes["schemes"] = diff["schemes"]

        if "utis" in diff:
            for uti, handler in diff["utis"].items():
                self.do.set_default_uti(uti, handler["to"])
            self.changes["utis"] = diff["utis"]

    def _output(self, ret=None):
        if ret is None:
            ret = {"changes": self.changes, "errors": self.errors}
        if "json" == self.fmt:
            return print(json.dumps(ret))
        return print(yaml.dump(ret))

    def _lookup_handler(self, handler):
        if handler not in self.handlers:
            self.handlers[handler] = (
                self.do.get_app_path(handler).fileSystemRepresentation().decode()
            )
        return self.handlers[handler]

    def _find_config(self, file=None):
        if file is None:
            xch = xdg_config_home()

            for path in (
                xch / "dooti.yaml",
                xch / "dooti.yml",
                xch / "dooti" / "dooti.yaml",
                xch / "dooti" / "dooti.yml",
                xch / "dooti" / "config.yaml",
                xch / "dooti" / "config.yml",
            ):
                if path.exists():
                    return path
            raise ValueError(f"Could not find dooti configuration in `{xch}`.")
        if not Path(file).exists():
            raise ValueError(
                f"Passed dooti configuration file `{file}` does not exist."
            )
        return file

    def _load_config(self, file):
        with open(file, encoding="utf-8") as f:
            definitions = yaml.load(f, Loader=yaml.Loader)

        if not isinstance(definitions, dict):
            raise ValueError("Invalid configuration, must be a dictionary.")
        if not any(x in definitions for x in ("app",) + self.scopes):
            raise ValueError(
                "Configuration does not contain any actionable definitions."
            )
        return definitions

    def _ask_consent(self, diffs):
        for atype, diff in diffs.items():
            if not diff:
                continue
            print(
                f"The following {atype[:-1]}{'s are' if len(diff) > 1 else ' is'} "
                "set to be changed:"
            )
            for name, change in diff.items():
                print(f"{name}: {change['from']} -> {change['to']}")
            print()
        try:
            return input("Do you want to continue? [y/n]: ").lower().startswith("y")
        except KeyboardInterrupt:
            print()
            return False


def main():
    """
    Prepare CLI args parser and hand off to DootiCLI
    """
    parser = argparse.ArgumentParser(
        prog="dooti", description="Manage default handlers on macOS."
    )
    parser.add_argument(
        "-f",
        "--format",
        help="The output format. Defaults to YAML.",
        dest="fmt",
        choices=("json", "yaml"),
    )
    parser.add_argument(
        "-y",
        "--yes",
        help="Do not ask for consent, assume yes.",
        dest="assume_yes",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--dry-run",
        help="Only show planned changes and exit.",
        dest="dry_run",
        action="store_true",
    )
    subparsers = parser.add_subparsers(help="commands")

    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply a YAML state configuration.",
    )
    apply_parser.add_argument(
        "-u",
        "--dynamic",
        action="store_true",
        help="Allow unregistered file extensions / dynamic UTIs.",
    )
    apply_parser.add_argument(
        "-i",
        "--file",
        help="Configuration to apply. If unspecified, searches in $XDG_CONFIG_HOME.",
    )
    apply_parser.set_defaults(func="apply_")

    ext_parser = subparsers.add_parser(
        "ext",
        help="Manage the default handler for all UTI associated with file extensions",
    )
    ext_parser.add_argument(
        "extensions", nargs="+", help="File extension(s) to operate on"
    )
    ext_parser.add_argument(
        "-u",
        "--dynamic",
        action="store_true",
        help="Allow unregistered file extensions / dynamic UTIs.",
    )
    ext_parser.add_argument(
        "-x",
        "--handler",
        help="The handler to associate with the file extensions. If unset, returns the default handler(s).",
    )
    ext_parser.set_defaults(func="ext")

    scheme_parser = subparsers.add_parser(
        "scheme", help="Manage default handler for URI scheme(s)"
    )
    scheme_parser.add_argument("schemes", nargs="+", help="Scheme(s) to operate on")
    scheme_parser.add_argument(
        "-x",
        "--handler",
        help="The handler to associate with the scheme(s). If unset, returns the default handler(s).",
    )
    scheme_parser.set_defaults(func="scheme")

    uti_parser = subparsers.add_parser("uti", help="Manage default handler for UTI(s)")
    uti_parser.add_argument("utis", nargs="+", help="UTI(s) to operate on")
    uti_parser.add_argument(
        "-x",
        "--handler",
        help="The handler to associate with the UTI(s). If unset, returns the default handler(s).",
    )
    uti_parser.set_defaults(func="uti")

    args = parser.parse_args()
    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()
    args = parser.parse_args()
    cli = DootiCLI(assume_yes=args.assume_yes, dry_run=args.dry_run, fmt=args.fmt)
    func = args.func
    del args.func
    del args.assume_yes
    del args.dry_run
    del args.fmt

    cli.run(func, args)


if __name__ == "__main__":
    main()
