import argparse
import json
import logging
import sys

import yaml

from .dooti import ApplicationNotFound, ExtHasNoRegisteredUTI, dooti

log = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="{levelname}: {message}", style="{"
)


def ext(extensions, dynamic, handler, fmt, assume_yes, dry_run):
    ret = {"changes": {}, "errors": []}

    do = dooti()
    current = {ext: do.get_default_ext(ext) for ext in extensions}

    if handler is None:
        return out(current, fmt)

    try:
        handler = do.get_app_path(handler).fileSystemRepresentation().decode()
    except ApplicationNotFound as err:
        ret["errors"].append(str(err))
        out(ret, fmt)
        return 1

    diff = {
        ext: {"from": current[ext], "to": handler}
        for ext in extensions
        if current[ext] != handler
    }

    if dry_run:
        ret["changes"]["extensions"] = diff
        return out(ret, fmt)
    if diff and not (assume_yes or _ask_consent({"extension": diff})):
        log.info("Did not get consent to apply changes. Exiting.")
        return 2

    errored = []
    for ext in diff:
        try:
            do.set_default_ext(ext, handler, allow_dynamic=dynamic)
        except ExtHasNoRegisteredUTI:
            errored.append(ext)
            ret["errors"].append(
                f"No UTI are registered for file extension '{ext}'. To force using a dynamic UTI, pass `-u`/`--dynamic`."
            )
    for errd in errored:
        del diff[errd]
    ret["changes"]["extensions"] = diff
    return out(ret, fmt)


def scheme(schemes, handler, fmt, assume_yes, dry_run):
    ret = {"changes": {}, "errors": []}

    do = dooti()
    current = {scheme: do.get_default_scheme(scheme) for scheme in schemes}

    if handler is None:
        return out(current, fmt)

    try:
        handler = do.get_app_path(handler).fileSystemRepresentation().decode()
    except ApplicationNotFound as err:
        ret["errors"].append(str(err))
        out(ret, fmt)
        return 1

    diff = {
        scheme: {"from": current[scheme], "to": handler}
        for scheme in schemes
        if current[scheme] != handler
    }

    if dry_run:
        ret["changes"]["schemes"] = diff
        return out(ret, fmt)
    if diff and not (assume_yes or _ask_consent({"scheme": diff})):
        log.info("Did not get consent to apply changes. Exiting.")
        return 2

    for scheme in diff:
        do.set_default_scheme(scheme, handler)
    ret["changes"]["schemes"] = diff
    return out(ret, fmt)


def uti(utis, handler, fmt, assume_yes, dry_run):
    ret = {"changes": {}, "errors": []}

    do = dooti()
    current = {uti: do.get_default_uti(uti) for uti in utis}

    if handler is None:
        return out(current, fmt)

    try:
        handler = do.get_app_path(handler).fileSystemRepresentation().decode()
    except ApplicationNotFound as err:
        ret["errors"].append(str(err))
        out(ret, fmt)
        return 1

    diff = {
        uti: {"from": current[uti], "to": handler}
        for uti in utis
        if current[uti] != handler
    }

    if dry_run:
        ret["changes"]["utis"] = diff
        return out(ret, fmt)
    if diff and not (assume_yes or _ask_consent({"uti": diff})):
        log.info("Did not get consent to apply changes. Exiting.")
        return 2

    for uti in diff:
        do.set_default_uti(uti, handler)
    ret["changes"]["utis"] = diff
    return out(ret, fmt)


def out(out, fmt):
    if "json" == fmt:
        return print(json.dumps(out))
    return print(yaml.dump(out))


def _ask_consent(diffs):
    for atype, diff in diffs.items():
        print(
            f"The following {atype}{'s are' if len(diff) > 1 else ' is'} set to be changed:"
        )
        for name, change in diff.items():
            print(f"{name}: {change['from']} -> {change['to']}")
        print()
    try:
        return input("Do you want to continue? [y/n]: ").lower().startswith("y")
    except KeyboardInterrupt:
        print()
        return False


def cli():
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
    ext_parser.set_defaults(func=ext)

    scheme_parser = subparsers.add_parser(
        "scheme", help="Manage default handler for URI scheme(s)"
    )
    scheme_parser.add_argument("schemes", nargs="+", help="Scheme(s) to operate on")
    scheme_parser.add_argument(
        "-x",
        "--handler",
        help="The handler to associate with the scheme(s). If unset, returns the default handler(s).",
    )
    scheme_parser.set_defaults(func=scheme)

    uti_parser = subparsers.add_parser("uti", help="Manage default handler for UTI(s)")
    uti_parser.add_argument("utis", nargs="+", help="UTI(s) to operate on")
    uti_parser.add_argument(
        "-x",
        "--handler",
        help="The handler to associate with the UTI(s). If unset, returns the default handler(s).",
    )
    uti_parser.set_defaults(func=uti)

    args = parser.parse_args()
    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()
    args = parser.parse_args()
    func = args.func
    del args.func
    return func(**vars(args))


if __name__ == "__main__":
    sys.exit(cli())
