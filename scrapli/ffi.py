"""scrapli.ffi"""

import os
import sys
from pathlib import Path

from scrapli.exceptions import LibScrapliException

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
        N/A

    """
    override_path = os.environ.get(LIBSCRAPLI_PATH_OVERRIDE_ENV)
    if override_path is not None:
        print(f"using libscrapli path override '{override_path}'")

        return override_path

    if sys.platform == "linux":
        lib_filename = f"libscrapli.so.{LIBSCRAPLI_VERSION}"
    elif sys.platform == "darwin":
        lib_filename = f"libscrapli.{LIBSCRAPLI_VERSION}.dylib"
    else:
        raise LibScrapliException("unsupported platform")

    cache_path = _get_libscrapli_cache_path()

    cached_lib_filename = f"{cache_path}/{lib_filename}"

    print(f"looking for libscrapli at '{cached_lib_filename}'")

    if Path(cached_lib_filename).exists():
        return cached_lib_filename

    print(
        f"libscrapli does not exist at path '{cached_lib_filename}',"
        " writing to disk at that location..."
    )

    _write_libscrapli_to_cache_path(cached_lib_filename)

    return cached_lib_filename


def _get_libscrapli_cache_path() -> str:
    override_path = os.environ.get(LIBSCRAPLI_PATH_OVERRIDE_ENV)
    if override_path is not None:
        print(f"using libscrapli cache path override '{override_path}'")

        return override_path

    if sys.platform == "linux":
        cache_dir = os.environ.get(XDG_CACHE_HOME_ENV)
        if cache_dir is None:
            cache_dir = f"{os.environ.get('HOME')}/.cache/scrapli"
    elif sys.platform == "darwin":
        cache_dir = f"{os.environ.get('HOME')}/Library/Caches/scrapli"
    else:
        raise LibScrapliException("unsupported platform")

    # TODO all the prints in here should be logging
    print(f"using libscrapli cache dir '{cache_dir}'")

    return cache_dir


def _write_libscrapli_to_cache_path(cached_lib_filename: str) -> str:
    # TODO obviously

    _ = cached_lib_filename

    raise NotImplementedError
