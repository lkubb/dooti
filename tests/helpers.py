import subprocess
import tempfile


def get_scheme_handler(scheme):
    return subprocess.check_output(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            f"ObjC.import('AppKit'); $.NSWorkspace.sharedWorkspace.URLForApplicationToOpenURL($.NSURL.URLWithString('{scheme}:')).path",
        ],
        text=True,
    ).strip()


def get_ext_handler(ext):
    with tempfile.NamedTemporaryFile(suffix=f".{ext}") as tmp:
        alias = subprocess.check_output(
            [
                "osascript",
                "-e",
                f'tell application "System Events" to get the default application of the file "{tmp.name}"',
            ],
            text=True,
        ).strip()
        return "/" + "/".join(alias.split(":")[1:-1])
