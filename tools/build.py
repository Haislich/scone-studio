#!/usr/bin/env python3

import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.getcwd())
CORES = multiprocessing.cpu_count() // 2
ROOT = Path(__file__).resolve().parent.parent
SUB = ROOT / "submodules"
DEPS = ROOT / "dependencies"

SUBDIRS = {
    "osg": SUB / "OpenSceneGraph",
    "simbody": SUB / "simbody",
    "opensim": SUB / "opensim3-scone",
    "scone": ROOT / "scone",
}

DEPSDIRS = {name: DEPS / name for name in SUBDIRS}

APT_PACKAGES = [
    # general
    "git",
    "rsync",
    "cmake",
    "make",
    "gcc",
    "g++",
    "python3.12-dev",
    "ruby",
    "ruby-dev",
    "rubygems",
    # osg
    "libpng-dev",
    "zlib1g-dev",
    "qtbase5-dev",
    # simbody
    "liblapack-dev",
    # scone
    "freeglut3-dev",
    "libxi-dev",
    "libxmu-dev",
    "liblapack-dev",
]


def run(cmd, cwd=None):
    print(f"\n>> Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd)


def ensure_dirs():
    SUB.mkdir(exist_ok=True)
    DEPS.mkdir(exist_ok=True)
    for d in DEPSDIRS.values():
        d.mkdir(exist_ok=True)


def install_system_deps():
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y"] + APT_PACKAGES)
    run(["sudo", "gem", "install", "--no-document", "fpm"])


def already_built(dep_name: str):
    install_path = DEPSDIRS[dep_name] / "install"
    return install_path.exists()


def cmake_configure_and_build(name: str, extra_flags=None):
    src = SUBDIRS[name]
    build = DEPSDIRS[name] / "build"
    install = DEPSDIRS[name] / "install"

    if build.exists():
        shutil.rmtree(build)
    build.mkdir()

    cmake_cmd = [
        "cmake",
        str(src),
        f"-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={install}",
        "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
    ]

    if extra_flags:
        cmake_cmd += extra_flags

    run(cmake_cmd, cwd=build)
    run(["cmake", "--build", ".", "--parallel", str(CORES)], cwd=build)
    run(["cmake", "--install", "."], cwd=build)


def build_osg(force=False):
    if already_built("osg") and not force:
        print("OSG already built. Use --rebuild to force.")
        return

    cmake_configure_and_build(
        "osg",
        extra_flags=[
            "-DOSG_USE_QT=ON",
            "-DDESIRED_QT_VERSION=5",
        ],
    )


def build_simbody(force=False):
    if already_built("simbody") and not force:
        print("Simbody already built. Use --rebuild to force.")
        return

    cmake_configure_and_build("simbody")


def build_opensim(force=False):
    if already_built("opensim") and not force:
        print("OpenSim already built. Use --rebuild to force.")
        return

    simbody_home = DEPSDIRS["simbody"] / "install"

    # PLATFORM-SPECIFIC FLAGS
    platform_flags = []
    if sys.platform == "darwin":  # macOS
        platform_flags = [
            "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.10",
            "-DCMAKE_CXX_FLAGS=-stdlib=libc++",
            "-DCMAKE_MACOSX_RPATH=TRUE",
            "-DCMAKE_INSTALL_RPATH=@executable_path/../lib",
            "-DBUILD_TESTING=OFF",
            "-DBUILD_API_EXAMPLES=OFF",
            "-DBUILD_API_ONLY=OFF",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]
    else:  # Linux
        platform_flags = [
            "-DCMAKE_INSTALL_RPATH=$ORIGIN",
            "-DBUILD_TESTING=OFF",
            "-DBUILD_API_EXAMPLES=OFF",
            "-DBUILD_API_ONLY=OFF",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]

    extra_flags = [
        f"-DSIMBODY_HOME={simbody_home}",
        "-DCMAKE_VERBOSE_MAKEFILE=FALSE",
    ] + platform_flags

    cmake_configure_and_build("opensim", extra_flags=extra_flags)


def build_scone(force=False):
    # SCONE is not considered "fixed", so always rebuild unless cached mode is implemented.
    cmake_configure_and_build("scone")


def build_all(force=False):
    build_osg(force)
    build_simbody(force)
    build_opensim(force)
    build_scone(force)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target", choices=["deps", "osg", "simbody", "opensim", "scone", "all"]
    )
    parser.add_argument("--rebuild", action="store_true")

    args = parser.parse_args()

    ensure_dirs()

    if args.target == "deps":
        install_system_deps()
    elif args.target == "osg":
        build_osg(args.rebuild)
    elif args.target == "simbody":
        build_simbody(args.rebuild)
    elif args.target == "opensim":
        build_opensim(args.rebuild)
    elif args.target == "scone":
        build_scone(args.rebuild)
    elif args.target == "all":
        build_all(args.rebuild)


if __name__ == "__main__":
    main()
