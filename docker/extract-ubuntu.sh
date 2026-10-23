#!/usr/bin/env bash
set -euo pipefail

# Extract the Meshroom bundle from the Ubuntu Meshroom image.
# See docker/common.sh for the environment variables.

# Work from the top level Meshroom directory, wherever the script is called from
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export OS=ubuntu
export OS_VERSION="${UBUNTU_VERSION:-22.04}"

exec docker/extract-image.sh
