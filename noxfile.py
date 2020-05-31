"""scrapli.noxfile"""
import re
from typing import Dict, List

import nox

nox.options.error_on_missing_interpreters = False
nox.options.stop_on_first_error = False

DEV_REQUIREMENTS: Dict[str, str] = {}

# this wouldn't work for other projects probably as its kinda hacky, but works just fine for scrapli
with open("requirements-dev.txt") as f:
    dev_requirements_lines: List[str] = [
        line for line in f.readlines() if not line.startswith("-r") or line.startswith("#")
    ]

for requirement in dev_requirements_lines:
    parsed_requirement = re.match(
        pattern=r"^([a-z0-9\-]+)([><=]{1,2}\S*)(?:.*)$", string=requirement, flags=re.I | re.M
    )
    DEV_REQUIREMENTS[parsed_requirement.groups()[0]] = parsed_requirement.groups()[1]


@nox.session(python=["3.6", "3.7", "3.8"])
def unit_tests(session):
    """
    Nox run unit tests

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install("-r", "requirements-dev.txt")
    session.run(
        "pytest",
        "--cov=scrapli",
        "--cov-report",
        "html",
        "--cov-report",
        "term",
        "tests/unit",
        "-v",
    )


@nox.session(python=["3.8"])
def isort(session):
    """
    Nox run isort

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install(f"isort{DEV_REQUIREMENTS['isort']}")
    session.run("isort", "-rc", "-c", ".")


@nox.session(python=["3.8"])
def black(session):
    """
    Nox run black

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install(f"black{DEV_REQUIREMENTS['black']}")
    session.run("black", "--check", ".")


@nox.session(python=["3.8"])
def pylama(session):
    """
    Nox run pylama

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install("-r", "requirements-dev.txt")
    session.install("-e", ".")
    session.run("pylama", ".")


@nox.session(python=["3.8"])
def pydocstyle(session):
    """
    Nox run pydocstyle

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install(f"pydocstyle{DEV_REQUIREMENTS['pydocstyle']}")
    session.run("pydocstyle", ".")


@nox.session(python=["3.8"])
def mypy(session):
    """
    Nox run mypy

    Args:
        session: nox session

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    session.install(f"mypy{DEV_REQUIREMENTS['mypy']}")
    session.run("mypy", "--strict", "scrapli/")
