#!/usr/bin/env bash
set -euo pipefail

# Build the Rocky Linux Meshroom images (deps + meshroom).
# See docker/common.sh for the environment variables.

export OS=rocky
export OS_VERSION="${ROCKY_VERSION:-9}"

exec docker/build-image.sh
