#!/usr/bin/env python
"""scrapli - ssh|telnet screen scraping client library"""
import setuptools

from scrapli import __version__

__author__ = "Carl Montanari"

with open("README.md", "r", encoding="utf-8") as f:
    README = f.read()

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
    with open(f"requirements-{extra}.txt", "r") as f:
        EXTRAS_REQUIRE[extra] = f.read().splitlines()

full_requirements = [requirement for extra in EXTRAS_REQUIRE.values() for requirement in extra]
EXTRAS_REQUIRE["full"] = full_requirements


setuptools.setup(
    name="scrapli",
    version=__version__,
    author=__author__,
    author_email="carl.r.montanari@gmail.com",
    description="Fast, flexible, sync/async, Python 3.6+ screen scraping client specifically for "
    "network devices",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/carlmontanari/scrapli",
    packages=setuptools.find_packages(),
    install_requires=[],
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.6",
)
