"""setup"""

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.editable_wheel import editable_wheel
from setuptools.command.sdist import sdist

LIBSCRAPLI_VERSION = "0.0.1-alpha.9"
LIBSCRAPLI_REPO = "https://github.com/scrapli/libscrapli"
LIBSCRAPLI_BUILD_PATH_ENV = "LIBSCRAPLI_BUILD_PATH"
LIBSCRPALI_ZIG_TRIPLE_ENV = "LIBSCRAPLI_ZIG_TRIPLE"

WHEEL_TARGETS = {
    # zig-triple <-> wheel
    "x86_64-macos": "macosx_11_0_x86_64",
    "aarch64-macos": "macosx_11_0_arm64",
    "x86_64-linux-gnu": "manylinux_x86_64",
    "x86_64-linux-musl": "musllinux_x86_64",
    "aarch64-linux-gnu": "manylinux_arm64",
    "aarch64-linux-musl": "musllinux_arm64",
}


class Libscrapli:
    """Dumb container for setup-related helpers"""

    _libscrapli_tag: Optional[str] = None

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

    @staticmethod
    def _get_zig_style_arch() -> str:
        p = platform.machine()

        if p == "amd64":
            return "x86_64"

        if p == "arm64":
            return "aarch64"

        raise NotImplementedError("unsupported platform")

    @staticmethod
    def _get_zig_style_platform() -> str:
        if sys.platform == "darwin":
            return "macos"

        if sys.platform == "linux":
            if os.path.exists("/lib/libc.musl-x86_64.so.1"):
                return "linux-musl"
            return "linux-gnu"

        raise NotImplementedError("unsupported platform")

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
    def _get_libscrapli_built_shared_object_filename(build_path: str) -> str:
        if sys.platform == "linux":
            lib_filenames = list(Path(build_path).glob("libscrapli.so.*"))
        elif sys.platform == "darwin":
            lib_filenames = list(Path(build_path).glob("libscrapli.*.dylib"))
        else:
            raise NotImplementedError("unsupported platform")

        if len(lib_filenames) != 1:
            raise OSError("not exactly one built shared library object")

        return lib_filenames[0].name

    @staticmethod
    def _get_libscrapli_output_shared_object_filename(version: str) -> str:
        if sys.platform == "linux":
            lib_filename = f"libscrapli.so.{version}"
        elif sys.platform == "darwin":
            lib_filename = f"libscrapli.{version}.dylib"
        else:
            raise NotImplementedError("unsupported platform")

        return lib_filename

    def _get_clone_command(self, tmp_build_dir: str) -> list[list[str]]:
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
                    "--depth",
                    "1",
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

    def _run_sdist_and_editable_wheel(self) -> None:
        src_lib_path = Path("scrapli/lib")

        libscrapli_build_path = self._get_libscrapli_build_path()

        if LIBSCRAPLI_BUILD_PATH_ENV not in os.environ:
            clone_commands = self._get_clone_command(tmp_build_dir=str(libscrapli_build_path))

            for clone_command in clone_commands:
                subprocess.check_call(clone_command)

            subprocess.check_call(
                self._get_build_command(all_targets=False),
                cwd=libscrapli_build_path,
            )

        built_lib_name = self._get_libscrapli_built_shared_object_filename(
            build_path=f"{libscrapli_build_path}/zig-out/native/"
        )
        out_lib_name = self._get_libscrapli_output_shared_object_filename(
            version=self.libscrapli_tag.lstrip("v")
        )

        built_lib = f"{libscrapli_build_path}/zig-out/native/{built_lib_name}"

        lib_dest = src_lib_path / out_lib_name
        shutil.copy2(built_lib, lib_dest)

        self._clean_libscrapli_build_path(libscrapli_build_path=libscrapli_build_path)


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

        libscrapli_build_path = self._get_libscrapli_build_path()

        if LIBSCRAPLI_BUILD_PATH_ENV not in os.environ:
            clone_commands = self._get_clone_command(tmp_build_dir=str(libscrapli_build_path))

            for clone_command in clone_commands:
                subprocess.check_call(clone_command)

            subprocess.check_call(
                # if no zig triple specified, then we are building for the current platform, so
                # don't build all the things
                self._get_build_command(all_targets=LIBSCRPALI_ZIG_TRIPLE_ENV in os.environ),
                cwd=libscrapli_build_path,
            )

        built_lib_name = self._get_libscrapli_built_shared_object_filename(
            build_path=f"{libscrapli_build_path}/zig-out/{zig_triple}"
        )
        out_lib_name = self._get_libscrapli_output_shared_object_filename(
            version=self.libscrapli_tag.lstrip("v")
        )

        built_lib = f"{libscrapli_build_path}/zig-out/{zig_triple}/{built_lib_name}"

        lib_dest = src_lib_path / out_lib_name
        shutil.copy2(built_lib, lib_dest)

        self._clean_libscrapli_build_path(libscrapli_build_path=libscrapli_build_path)

        super().run()


setup(
    cmdclass={
        "sdist": LibscrapliSdist,
        "editable_wheel": LibscrapliEditableWheel,
        "bdist_wheel": LibscrapliBdist,
    },
)
