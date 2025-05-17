"""scrapli.helper"""

from pathlib import Path

from scrapli.exceptions import OperationException


def resolve_file(file: str) -> str:
    """
    Resolve file from provided string

    Args:
        file: string path to file

    Returns:
        str: resolved/expanded (if applicable) string path to file

    Raises:
        OperationException: if file cannot be resolved

    """
    if Path(file).is_file():
        return str(Path(file))
    if Path(file).expanduser().is_file():
        return str(Path(file).expanduser())

    raise OperationException(f"path `{file}` could not be resolved")
