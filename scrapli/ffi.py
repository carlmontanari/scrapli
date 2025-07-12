"""scrapli.ffi"""

import importlib.resources
import os
import sys
from logging import getLogger
from pathlib import Path

from scrapli.exceptions import LibScrapliException

logger = getLogger(__name__)

LIBSCRAPLI_VERSION = "0.0.1-alpha.17"
LIBSCRAPLI_PATH_OVERRIDE_ENV = "LIBSCRAPLI_PATH"
LIBSCRAPLI_CACHE_PATH_OVERRIDE_ENV = "LIBSCRAPLI_CACHE_PATH"
XDG_CACHE_HOME_ENV = "XDG_CACHE_HOME"


def get_libscrapli_shared_object_filename(version: str = LIBSCRAPLI_VERSION) -> str:
    """
    Returns the name of the libscrapli shared object for the given version/platform.

    Args:
        version: the libscrapli version

    Returns:
        str: filename of the shared object

    Raises:
        LibScrapliException: if unsupported platform

    """
    if sys.platform == "linux":
        lib_filename = f"libscrapli.so.{version}"
    elif sys.platform == "darwin":
        lib_filename = f"libscrapli.{version}.dylib"
    else:
        raise LibScrapliException("unsupported platform")

    return lib_filename


def get_libscrapli_path() -> str:
    """
    Returns the file path to the libscrapli shared library.

    Attempts to load from override paths or from installed path in scrapli itself -- this would be
    either the shared object(s) from source (i.e. cloning the repo) or from the installation either
    via a wheel or sdist.

    Args:
        N/A

    Returns:
        str: libscrapli shared library path

    Raises:
        LibScrapliException: if libscrapli is not found at override path or default installation
            path

    """
    override_path = os.environ.get(LIBSCRAPLI_PATH_OVERRIDE_ENV)
    if override_path is not None:
        logger.debug("using libscrapli path override '%s'", override_path)

        return override_path

    source_lib_dir = importlib.resources.files("scrapli.lib")
    source_lib_filename = f"{source_lib_dir}/{get_libscrapli_shared_object_filename()}"

    logger.debug("loading libscrapli from scrapli installation '%s'", source_lib_filename)

    if Path(source_lib_filename).exists():
        return source_lib_filename

    raise LibScrapliException("libscrapli not available")
