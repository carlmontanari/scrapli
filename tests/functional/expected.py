import os
from pathlib import Path

PYTEST_CURRENT_TEST = "PYTEST_CURRENT_TEST"


def write_expected(f: str, result: str):
    expected_dir = Path(os.path.abspath(f)).parent

    current_test = os.getenv(PYTEST_CURRENT_TEST).split("::")[-1].split(" ")[0]

    with open(f"{expected_dir}/expected/{current_test}", "w") as out:
        out.write(result)


def get_expected(f: str) -> str:
    expected_dir = Path(os.path.abspath(f)).parent

    current_test = os.getenv(PYTEST_CURRENT_TEST).split("::")[-1].split(" ")[0]

    try:
        with open(f"{expected_dir}/expected/{current_test}", "r") as out:
            return out.read()
    except NotADirectoryError:
        return ""
