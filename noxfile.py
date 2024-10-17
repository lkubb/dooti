import os
import shutil
from pathlib import Path

import nox

REPO_ROOT = Path(__file__).resolve().parent
SKIP_REQUIREMENTS_INSTALL = os.environ.get("SKIP_REQUIREMENTS_INSTALL", "0") == "1"


def _install(session, *args):
    if SKIP_REQUIREMENTS_INSTALL:
        return
    session.install(*args)


@nox.session(python="3")
def docs(session):
    """
    Build Docs
    """
    _install(session, ".[docs]")
    os.chdir("docs/")
    session.run("make", "clean", external=True)
    session.run("make", "linkcheck", "SPHINXOPTS=-W", external=True)
    session.run("make", "html", "SPHINXOPTS=-W", external=True)
    os.chdir(str(REPO_ROOT))


@nox.session(name="docs-dev", python="3")
def docs_dev(session):
    """
    Rebuild docs on changes (live preview).
    """
    _install(session, ".[docs,docsauto]")
    build_dir = Path("docs", "_build", "html")

    # Allow specifying sphinx-autobuild options, like --host.
    args = ["--watch", "."] + session.posargs
    if not any(arg.startswith("--host") for arg in args):
        # If the user is overriding the host to something other than localhost,
        # it's likely they are rendering on a remote/headless system and don't
        # want the browser to open.
        args.append("--open-browser")
    args += ["docs", str(build_dir)]

    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
