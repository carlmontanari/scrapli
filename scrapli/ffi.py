"""scrapli.ffi"""

import os
import sys
from logging import getLogger
from pathlib import Path

from scrapli.exceptions import LibScrapliException

logger = getLogger(__name__)

LIBSCRAPLI_VERSION = "0.0.1-alpha.1"
LIBSCRAPLI_PATH_OVERRIDE_ENV = "LIBSCRAPLI_PATH"
LIBSCRAPLI_CACHE_PATH_OVERRIDE_ENV = "LIBSCRAPLI_CACHE_PATH"
XDG_CACHE_HOME_ENV = "XDG_CACHE_HOME"


def get_libscrapli_path() -> str:
    """
    Returns the file path to the libscrapli shared library.

    Attempts to load from override paths or the user/xdg cache directory.

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

    if sys.platform == "linux":
        lib_filename = f"libscrapli.so.{LIBSCRAPLI_VERSION}"
    elif sys.platform == "darwin":
        lib_filename = f"libscrapli.{LIBSCRAPLI_VERSION}.dylib"
    else:
        raise LibScrapliException("unsupported platform")

    cache_path = _get_libscrapli_cache_path()

    cached_lib_filename = f"{cache_path}/{lib_filename}"

    logger.debug("looking for libscrapli at '%s'", cached_lib_filename)

    if Path(cached_lib_filename).exists():
        return cached_lib_filename

    raise LibScrapliException(f"libscrapli does not exist at path '{cached_lib_filename}")


def _get_libscrapli_cache_path() -> str:
    override_path = os.environ.get(LIBSCRAPLI_PATH_OVERRIDE_ENV)
    if override_path is not None:
        logger.debug("using libscrapli cache path override '%s'", override_path)

        return override_path

    if sys.platform == "linux":
        cache_dir = os.environ.get(XDG_CACHE_HOME_ENV)
        if cache_dir is None:
            cache_dir = f"{os.environ.get('HOME')}/.cache/scrapli"
    elif sys.platform == "darwin":
        cache_dir = f"{os.environ.get('HOME')}/Library/Caches/scrapli"
    else:
        raise LibScrapliException("unsupported platform")

    logger.debug("using libscrapli cache dir '%s'", cache_dir)

    return cache_dir
