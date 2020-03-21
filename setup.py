#!/usr/bin/env python
"""scrapli - ssh|telnet screen scraping client library"""
import setuptools

__author__ = "Carl Montanari"

with open("README.md", "r") as f:
    README = f.read()

setuptools.setup(
    name="scrapli",
    version="2020.03.21",
    author=__author__,
    author_email="carl.r.montanari@gmail.com",
    description="Screen scraping (ssh|telnet) client focused on network devices",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/carlmontanari/scrapli",
    packages=setuptools.find_packages(),
    install_requires=[],
    extras_require={
        "textfsm": ["textfsm>=1.1.0", "ntc-templates>=1.1.0"],
        "paramiko": ["paramiko>=2.6.0"],
        "ssh2": ["ssh2-python>=0.18.0-1"],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.6",
)
