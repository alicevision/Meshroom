#!/usr/bin/env bash
set -euo pipefail

# Build the Ubuntu Meshroom images (deps + meshroom).
# See docker/common.sh for the environment variables.

export OS=ubuntu
export OS_VERSION="${UBUNTU_VERSION:-22.04}"

exec docker/build-image.sh
