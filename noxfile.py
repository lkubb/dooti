# pylint: disable=missing-function-docstring,protected-access
import os
import shutil
import sys
from importlib import metadata
from pathlib import Path

import nox

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

REPO_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
COVERAGE_REPORT_DB = REPO_ROOT / ".coverage"
COVERAGE_REPORT_PROJECT = "coverage-project.xml"
COVERAGE_REPORT_TESTS = "coverage-tests.xml"

SKIP_REQUIREMENTS_INSTALL = os.environ.get("SKIP_REQUIREMENTS_INSTALL", "0") == "1"
PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13")


nox.options.reuse_existing_virtualenvs = True

# Speed up all sessions by using uv if possible
if tuple(map(int, metadata.version("nox").split("."))) >= (2024, 3):
    nox.options.default_venv_backend = "uv|virtualenv"


def _install(session, *args):
    if SKIP_REQUIREMENTS_INSTALL:
        return
    session.install(*args)


@nox.session(python="3")
def docs(session):
    """
    Build Docs
    """
    _install(session, "-e", ".[docs]")
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
    _install(session, "-e", ".[docs,docsauto]")
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


@nox.session(python="3")
def tests(session):
    return _tests(session)


@nox.session(python=PYTHON_VERSIONS)
def tests_all(session):
    return _tests(session)


def _tests(session):  # pylint: disable=too-many-branches
    _install(session, "-e", ".[tests]")

    interpreter_version = session.python
    if interpreter_version == "3":
        interpreter_version += f".{sys.version_info.minor}"

    env = {
        "COVERAGE_FILE": str(COVERAGE_REPORT_DB),
    }

    args = [
        "--rootdir",
        str(REPO_ROOT),
        "--showlocals",
        "-ra",
        "-s",
    ]
    if session._runner.global_config.forcecolor:
        args.append("--color=yes")
    if not session.posargs:
        args.append("tests/")
    else:
        for arg in session.posargs:
            if arg.startswith("--color") and args[0].startswith("--color"):
                args.pop(0)
            args.append(arg)
        for arg in session.posargs:
            if arg.startswith("-"):
                continue
            if arg.startswith(f"tests{os.sep}"):
                break
            try:
                Path(arg).resolve().relative_to(REPO_ROOT / "tests")
                break
            except ValueError:
                continue
        else:
            args.append("tests/")
    session.run("coverage", "erase")
    try:
        session.run("coverage", "run", "-m", "pytest", *args, env=env)
    finally:
        session.run(
            "coverage",
            "xml",
            "-o",
            str(ARTIFACTS_DIR / interpreter_version / COVERAGE_REPORT_PROJECT),
            "--omit=tests/*",
            "--include=src/dooti/*",
        )
        session.run(
            "coverage",
            "xml",
            "-o",
            str(ARTIFACTS_DIR / interpreter_version / COVERAGE_REPORT_TESTS),
            "--omit=src/dooti/*",
            "--include=tests/*",
        )
        try:
            session.run(
                "coverage", "report", "--show-missing", "--include=src/dooti/*,tests/*"
            )
        finally:
            if COVERAGE_REPORT_DB.exists():
                shutil.move(
                    str(COVERAGE_REPORT_DB),
                    str(ARTIFACTS_DIR / interpreter_version / COVERAGE_REPORT_DB.name),
                )
