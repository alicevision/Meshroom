#!/usr/bin/env bash
set -euo pipefail

# Extract the Meshroom bundle from the Rocky Linux Meshroom image.
# See docker/common.sh for the environment variables.

export OS=rocky
export OS_VERSION="${ROCKY_VERSION:-9}"

exec docker/extract-image.sh
