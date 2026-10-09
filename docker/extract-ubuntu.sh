#!/usr/bin/env bash
set -euo pipefail

# Extract the Meshroom bundle from the Ubuntu Meshroom image.
# See docker/common.sh for the environment variables.

export OS=ubuntu
export OS_VERSION="${UBUNTU_VERSION:-22.04}"

exec docker/extract-image.sh
