#!/usr/bin/env bash
set -euo pipefail

# Build all supported Meshroom images. AV_VERSION must be set.

# Work from the top level Meshroom directory, wherever the script is called from
cd "$(dirname "${BASH_SOURCE[0]}")/.."

CUDA_VERSION=12.8.0 UBUNTU_VERSION=22.04 docker/build-ubuntu.sh
CUDA_VERSION=12.8.0 ROCKY_VERSION=9 docker/build-rocky.sh
