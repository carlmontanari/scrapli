import subprocess
from pathlib import Path

import pytest

CLI_EXAMPLES = list(Path("examples/cli").glob("*"))
NETCONF_EXAMPLES = list(Path("examples/netconf").glob("*"))


@pytest.mark.parametrize(
    argnames="example",
    argvalues=[e.name for e in CLI_EXAMPLES],
    ids=[e.name for e in CLI_EXAMPLES],
)
def test_cli_examples(example):
    subprocess.run(
        ["python3", str(Path("examples/cli") / example / "main.py")],
        check=True,
    )


@pytest.mark.parametrize(
    argnames="example",
    argvalues=[e.name for e in NETCONF_EXAMPLES],
    ids=[e.name for e in NETCONF_EXAMPLES],
)
def test_netconf_examples(example):
    subprocess.run(
        ["python3", str(Path("examples/netconf") / example / "main.py")],
        check=True,
    )
