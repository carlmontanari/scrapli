"""scrapli.ffi"""

import ctypes
import importlib.resources
import os
import platform
import sys
from logging import getLogger
from pathlib import Path

from scrapli.exceptions import LibScrapliException

logger = getLogger(__name__)

LIBSCRAPLI_VERSION = "0.0.1-rc.35"
LIBSCRAPLI_PATH_OVERRIDE_ENV = "LIBSCRAPLI_PATH"
LIBSCRAPLI_CACHE_PATH_OVERRIDE_ENV = "LIBSCRAPLI_CACHE_PATH"
XDG_CACHE_HOME_ENV = "XDG_CACHE_HOME"


def _is_musl() -> bool:
    try:
        ctypes.CDLL(None).gnu_get_libc_version
    except (AttributeError, OSError):
        return True

    return False


def _get_zig_style_arch() -> str:
    """
    Returns the zig-style arch name for the current machine.

    Args:
        N/A

    Returns:
        str: the zig-style arch name

    Raises:
        LibScrapliException: if unsupported arch

    """
    p = platform.machine()

    if p in {"amd64", "x86_64"}:
        return "x86_64"

    if p in {"arm64", "aarch64"}:
        return "aarch64"

    raise LibScrapliException(f"unsupported arch '{p}'")


def get_libscrapli_shared_object_filename(version: str = LIBSCRAPLI_VERSION) -> str:
    """
    Returns the name of the libscrapli shared object for the given version/platform.

    The name is fully qualified -- as in it includes the arch/platform (and abi for linux) -- this
    mirrors the release asset naming (sans any "dynamic-" marker) and how scrapligo caches
    libscrapli, and ensures shared objects for different targets never collide on disk.

    Args:
        version: the libscrapli version

    Returns:
        str: filename of the shared object

    Raises:
        LibScrapliException: if unsupported platform

    """
    if sys.platform == "linux":
        abi = "musl" if _is_musl() else "gnu"
        lib_filename = f"libscrapli-{_get_zig_style_arch()}-linux-{abi}.so.{version}"
    elif sys.platform == "darwin":
        lib_filename = f"libscrapli-{_get_zig_style_arch()}-macos.{version}.dylib"
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
