#!/usr/bin/env python
"""scrapli"""
from pathlib import Path

import setuptools

__version__ = "2022.01.30.post1"
__author__ = "Carl Montanari"

with open("README.md", "r", encoding="utf-8") as f:
    README = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    INSTALL_REQUIRES = f.read().splitlines()

EXTRAS_REQUIRE = {
    "textfsm": [],
    "genie": [],
    "ttp": [],
    "paramiko": [],
    "ssh2": [],
    "asyncssh": [],
    "community": [],
}

for extra in EXTRAS_REQUIRE:
    with open(f"requirements-{extra}.txt", "r", encoding="utf-8") as f:
        # drops the version cap on pins but lets us keep it in the extras requirements files
        # such that CI can be more deterministic and dependabot notifications are more useful
        pins = [pin.partition(",<")[0] if ",<" in pin else pin for pin in f.read().splitlines()]

        EXTRAS_REQUIRE[extra] = pins

full_requirements = [requirement for extra in EXTRAS_REQUIRE.values() for requirement in extra]
EXTRAS_REQUIRE["full"] = full_requirements


def get_packages(package):
    """Return root package and all sub-packages"""
    return [str(path.parent) for path in Path(package).glob("**/__init__.py")]


setuptools.setup(
    name="scrapli",
    version=__version__,
    author=__author__,
    author_email="carl.r.montanari@gmail.com",
    description="Fast, flexible, sync/async, Python 3.7+ screen scraping client specifically for "
    "network devices",
    long_description=README,
    long_description_content_type="text/markdown",
    keywords="ssh telnet netconf automation network cisco iosxr iosxe nxos arista eos juniper "
    "junos",
    url="https://github.com/carlmontanari/scrapli",
    project_urls={
        "Changelog": "https://carlmontanari.github.io/scrapli/changelog",
        "Docs": "https://carlmontanari.github.io/scrapli/",
    },
    license="MIT",
    package_data={"scrapli": ["py.typed"]},
    packages=get_packages("scrapli"),
    install_requires=INSTALL_REQUIRES,
    dependency_links=[],
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    # zip_safe False for mypy
    # https://mypy.readthedocs.io/en/stable/installed_packages.html
    zip_safe=False,
)
