"""
noxfile.py

in our case just used for handily running linting/unit testing on all the target python versions
locally
"""

import nox

nox.options.stop_on_first_error = False
nox.options.default_venv_backend = "venv"


@nox.session(python=["3.10", "3.11", "3.12", "3.13", "3.14"])
def lint(session: nox.sessions.Session) -> None:
    """
    Nox run linters

    Args:
        session: nox session

    Returns:
        None

    Raises:
        N/A

    """
    session.install("-U", "setuptools", "wheel", "pip")
    session.install("-r", "requirements-dev.txt")
    session.run("make", "lint")


@nox.session(python=["3.10", "3.11", "3.12", "3.13", "3.14"])
def unit_tests(session: nox.sessions.Session) -> None:
    """
    Nox run unit tests

    Args:
        session: nox session

    Returns:
        None

    Raises:
        N/A

    """
    session.install("-U", "setuptools", "wheel", "pip")
    session.install("-r", "requirements-dev.txt")
    session.install("-r", "requirements-textfsm.txt")
    session.install(".")
    session.run("make", "test")
