"""setup"""

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from http import HTTPStatus
from pathlib import Path
from urllib.request import urlopen

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.editable_wheel import editable_wheel
from setuptools.command.sdist import sdist

LIBSCRAPLI_VERSION = "0.0.1-alpha.17"
LIBSCRAPLI_REPO = "https://github.com/scrapli/libscrapli"
LIBSCRAPLI_BUILD_PATH_ENV = "LIBSCRAPLI_BUILD_PATH"
LIBSCRPALI_ZIG_TRIPLE_ENV = "LIBSCRAPLI_ZIG_TRIPLE"

# if set to anything, always build libscrapli, as in: dont just slurp down the artifacts
# from a release
LIBSCRAPLI_ALWAYS_BUILD_ENV = "LIBSCRAPLI_ALWAYS_BUILD"
LIBSCRAPLI_ALWAYS_BUILD = (
    True if os.getenv(LIBSCRAPLI_ALWAYS_BUILD_ENV, None) is not None else False
)

WHEEL_TARGETS = {
    # zig-triple <-> wheel
    "x86_64-macos": "macosx_11_0_x86_64",
    "aarch64-macos": "macosx_11_0_arm64",
    "x86_64-linux-gnu": "manylinux2010_x86_64",
    "x86_64-linux-musl": "musllinux_1_1_x86_64",
    "aarch64-linux-gnu": "manylinux2014_aarch64",
    "aarch64-linux-musl": "musllinux_1_1_aarch64",
}


class Libscrapli:
    """Dumb container for setup-related helpers"""

    _libscrapli_tag: str | None = None
    _libscrapli_version_is_release: bool | None = None

    @property
    def libscrapli_tag(self) -> str:
        """
        Return the libscrapli version/tag

        Args:
            N/A

        Returns:
            str: the parsed libscrapli verison/tag

        Raises:
            N/A

        """
        if self._libscrapli_tag is not None:
            return self._libscrapli_tag

        self._libscrapli_tag = (
            f"v{LIBSCRAPLI_VERSION}"
            if not re.fullmatch(r"[0-9a-f]{7,40}", LIBSCRAPLI_VERSION)
            else LIBSCRAPLI_VERSION
        )

        return self._libscrapli_tag

    @property
    def libscrapli_is_release_tag(self) -> bool:
        """
        Return true if the target libscrapli version is a released version, othewrise false

        Args:
            N/A

        Returns:
            bool: true if a released (semver) version

        Raises:
            N/A

        """
        if self._libscrapli_version_is_release is not None:
            return self._libscrapli_version_is_release

        if self.libscrapli_tag == "" or re.fullmatch(r"[0-9a-f]{7,40}", self.libscrapli_tag):
            self._libscrapli_version_is_release = False
        else:
            self._libscrapli_version_is_release = True

        return self._libscrapli_version_is_release

    @staticmethod
    def _get_zig_style_arch() -> str:
        p = platform.machine()

        if p in {"amd64", "x86_64"}:
            return "x86_64"

        if p in {"arm64", "aarch64"}:
            return "aarch64"

        raise NotImplementedError(f"unsupported platform '{p}'")

    @staticmethod
    def _get_zig_style_platform() -> str:
        if sys.platform == "darwin":
            return "macos"

        if sys.platform == "linux":
            if os.path.exists("/lib/libc.musl-x86_64.so.1"):
                return "linux-musl"
            return "linux-gnu"

        raise NotImplementedError(f"unsupported platform '{sys.platform}'")

    @staticmethod
    def _get_libscrapli_build_path() -> Path:
        if libscrapli_build_path := os.environ.get(LIBSCRAPLI_BUILD_PATH_ENV):
            return Path(libscrapli_build_path)

        return Path(tempfile.mkdtemp())

    @staticmethod
    def _clean_libscrapli_build_path(libscrapli_build_path: Path) -> None:
        if LIBSCRAPLI_BUILD_PATH_ENV in os.environ:
            # build path env set, likely in ci, dont clean up as we may need it for
            # building other wheels. ci will/should clean it
            return

        shutil.rmtree(libscrapli_build_path)

    @staticmethod
    def _get_libscrapli_output_shared_object_filename() -> str:
        p = sys.platform

        zig_triple = os.environ.get(LIBSCRPALI_ZIG_TRIPLE_ENV, None)
        if zig_triple is not None:
            # probably building all the wheels, we dont actually want the shared object
            # for our current system, we want it for the target triple
            if "linux" in zig_triple:
                p = "linux"
            else:
                p = "darwin"

        if p == "linux":
            lib_filename = f"libscrapli.so.{LIBSCRAPLI_VERSION}"
        elif p == "darwin":
            lib_filename = f"libscrapli.{LIBSCRAPLI_VERSION}.dylib"
        else:
            raise NotImplementedError("unsupported platform")

        return lib_filename

    def _get_libscrapli_built_shared_object_filename(self, build_path: str) -> str:
        if self.libscrapli_is_release_tag:
            return str(Path(build_path) / self._get_libscrapli_output_shared_object_filename())

        # if we aren't a release the built object will still be named like foo.1.2.3, so we gotta
        # snag it by globbing since we dont know
        built_objects = list(Path(build_path).glob("libscrapli.*"))
        if len(built_objects) != 1:
            raise OSError("expecting exactly one built object...")

        return str(built_objects[0])

    @classmethod
    def _get_libscrapli_asset_filename(cls) -> str:
        zig_triple = os.environ.get(LIBSCRPALI_ZIG_TRIPLE_ENV, None)
        if zig_triple is not None:
            ext = "so" if "linux" in zig_triple else "dylib"
            return f"libscrapli-{zig_triple}.{ext}.{LIBSCRAPLI_VERSION}"

        _base = f"libscrapli-{cls._get_zig_style_arch()}"

        if sys.platform == "linux":
            lib_filename = f"{_base}-{cls._get_zig_style_platform()}.so.{LIBSCRAPLI_VERSION}"
        elif sys.platform == "darwin":
            lib_filename = f"{_base}-macos.dylib.{LIBSCRAPLI_VERSION}"
        else:
            raise NotImplementedError("unsupported platform")

        return lib_filename

    def _get_clone_command(self, tmp_build_dir: str) -> list[list[str]]:
        if self.libscrapli_is_release_tag:
            return [
                [
                    "git",
                    "clone",
                    "--branch",
                    self.libscrapli_tag,
                    "--depth",
                    "1",
                    "--single-branch",
                    LIBSCRAPLI_REPO,
                    tmp_build_dir,
                ]
            ]

        if self.libscrapli_tag == "":
            # unset means pull main
            return [
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    LIBSCRAPLI_REPO,
                    tmp_build_dir,
                ]
            ]

        if re.fullmatch(r"[0-9a-f]{7,40}", self.libscrapli_tag):
            # specific hash not main, not a release
            return [
                [
                    "git",
                    "clone",
                    LIBSCRAPLI_REPO,
                    tmp_build_dir,
                ],
                [
                    "git",
                    "-C",
                    tmp_build_dir,
                    "checkout",
                    self.libscrapli_tag,
                ],
            ]

        raise OSError("libscrapli tag is not a release tag, a hash, or empty (for build from main)")

    @staticmethod
    def _get_build_command(all_targets: bool = False) -> list[str]:
        cmd = [
            sys.executable,
            "-m",
            "ziglang",
            "build",
            "-freference-trace",
            "--summary",
            "all",
            "--",
            "--release",  # release mode
        ]

        if all_targets:
            cmd.append("--all-targets")

        return cmd

    def _download_asset(self, lib_dest: Path) -> None:
        _base = f"{LIBSCRAPLI_REPO}/releases/download/{self.libscrapli_tag}"
        _filename = self._get_libscrapli_asset_filename()
        asset_url = f"{_base}/{_filename}"

        with urlopen(asset_url) as response:
            if response.status != HTTPStatus.OK:
                raise OSError(f"failed downloading asset file at url '{asset_url}'")
            with open(lib_dest, mode="wb") as f:
                shutil.copyfileobj(response, f)

    def _build_from_source(self, lib_dest: Path) -> None:
        if LIBSCRPALI_ZIG_TRIPLE_ENV in os.environ:
            zig_triple = os.environ[LIBSCRPALI_ZIG_TRIPLE_ENV]
            wheel_platform = WHEEL_TARGETS[zig_triple]

            # we *technically* have a pure python package meaning we can lie to bdist_wheel and tell
            # it what our platform should be. so do that. we are "pure" python because we have no
            #  c-extensions, only the pre compiled zig shared object (i.e. .so or .dylib)
            self.plat_name_supplied = True
            self.plat_name = wheel_platform
        else:
            # not set in env, so not in ci, just do native/current platform like normal, but we
            # still need to know what that is so we grab the correct built shared object
            zig_triple = "native"

        libscrapli_build_path = self._get_libscrapli_build_path()

        if not Path(f"{libscrapli_build_path}/build.zig").exists():
            clone_commands = self._get_clone_command(tmp_build_dir=str(libscrapli_build_path))

            for clone_command in clone_commands:
                subprocess.check_call(clone_command)

            subprocess.check_call(
                # if no zig triple specified, then we are building for the current platform, so
                # don't build all the things
                self._get_build_command(all_targets=LIBSCRPALI_ZIG_TRIPLE_ENV in os.environ),
                cwd=libscrapli_build_path,
            )

        built_lib = self._get_libscrapli_built_shared_object_filename(
            build_path=f"{libscrapli_build_path}/zig-out/{zig_triple}/"
        )

        shutil.copy2(built_lib, lib_dest)

        self._clean_libscrapli_build_path(libscrapli_build_path=libscrapli_build_path)

    def _run_sdist_and_editable_wheel(self) -> None:
        src_lib_path = Path("scrapli/lib")
        out_lib_name = self._get_libscrapli_output_shared_object_filename()
        lib_dest = src_lib_path / out_lib_name

        if not LIBSCRAPLI_ALWAYS_BUILD and Path(src_lib_path / out_lib_name).exists():
            # requested target already exists, dont waste time building
            return

        if not LIBSCRAPLI_ALWAYS_BUILD and self.libscrapli_is_release_tag:
            self._download_asset(lib_dest=lib_dest)
        else:
            self._build_from_source(lib_dest=lib_dest)


class LibscrapliSdist(sdist, Libscrapli):  # type: ignore
    """Setuptools sdist dispatcher"""

    def run(self) -> None:
        """Run the sdist install"""
        self._run_sdist_and_editable_wheel()
        super().run()


class LibscrapliEditableWheel(editable_wheel, Libscrapli):  # type: ignore
    """Setuptools editable wheel dispatcher"""

    def run(self) -> None:
        """Run the editable wheel install"""
        self._run_sdist_and_editable_wheel()
        super().run()


class LibscrapliBdist(bdist_wheel, Libscrapli):  # type: ignore
    """Setuptools bdist dispatcher"""

    def run(self) -> None:
        """Run the bdist install"""
        if LIBSCRPALI_ZIG_TRIPLE_ENV in os.environ:
            zig_triple = os.environ[LIBSCRPALI_ZIG_TRIPLE_ENV]
            wheel_platform = WHEEL_TARGETS[zig_triple]

            # we *technically* have a pure python package meaning we can lie to bdist_wheel and tell
            # it what our platform should be. so do that. we are "pure" python because we have no
            #  c-extensions, only the pre compiled zig shared object (i.e. .so or .dylib)
            self.plat_name_supplied = True
            self.plat_name = wheel_platform
        else:
            # not set in env, so not in ci, just do native/current platform like normal, but we
            # still need to know what that is so we grab the correct built shared object
            zig_triple = "native"

        src_lib_path = Path("scrapli/lib")
        out_lib_name = self._get_libscrapli_output_shared_object_filename()
        lib_dest = src_lib_path / out_lib_name

        if not LIBSCRAPLI_ALWAYS_BUILD and Path(src_lib_path / out_lib_name).exists():
            # requested target already exists, dont waste time building
            super().run()

            return
        elif not LIBSCRAPLI_ALWAYS_BUILD and self.libscrapli_is_release_tag:
            self._download_asset(lib_dest=lib_dest)
        else:
            self._build_from_source(lib_dest=lib_dest)

        super().run()


setup(
    cmdclass={
        "sdist": LibscrapliSdist,
        "editable_wheel": LibscrapliEditableWheel,
        "bdist_wheel": LibscrapliBdist,
    },
)
