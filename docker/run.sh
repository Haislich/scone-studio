#!/usr/bin/env bash
set -euo pipefail

cd "$GITHUB_WORKSPACE"

echo "[run] building SCONE"
./tools/unix_2d_build-scone

echo "[run] rearranging binaries"
./tools/linux_3_create-install-dirtree

echo "[run] packaging deb"
./tools/linux_4_package
