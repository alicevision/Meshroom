#!/bin/sh

set -e

test -d docker || (
        echo This script must be run from the top level Meshroom directory
	exit 1
)

CUDA_VERSION=12.1.0 UBUNTU_VERSION=22.04 docker/build-ubuntu.sh

CUDA_VERSION=12.1.0 ROCKY_VERSION=9 docker/build-rocky.sh