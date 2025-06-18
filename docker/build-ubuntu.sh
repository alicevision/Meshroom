#!/bin/bash
set -e

test -z "$MESHROOM_VERSION" && MESHROOM_VERSION="$(git rev-parse --abbrev-ref HEAD)-$(git rev-parse --short HEAD)"
test -z "$AV_VERSION" && echo "AliceVision version not specified, set AV_VERSION in the environment" && exit 1
test -z "$CUDA_VERSION" && CUDA_VERSION=12.1.0
test -z "$UBUNTU_VERSION" && UBUNTU_VERSION=22.04

test -d docker || (
        echo This script must be run from the top level Meshroom directory
	exit 1
)

test -d dl || \
	mkdir dl
test -f dl/qt.run || \
        wget --no-check-certificate "https://download.qt.io/official_releases/online_installers/qt-unified-linux-x64-online.run" -O "dl/qt.run"

# DEPENDENCIES
docker build \
	--rm \
	--build-arg "CUDA_VERSION=${CUDA_VERSION}" \
	--build-arg "UBUNTU_VERSION=${UBUNTU_VERSION}" \
	--build-arg "AV_VERSION=${AV_VERSION}" \
	--tag "alicevision/meshroom-deps:${MESHROOM_VERSION}-av${AV_VERSION}-ubuntu${UBUNTU_VERSION}-cuda${CUDA_VERSION}" \
	-f docker/Dockerfile_ubuntu_deps .

# Meshroom
docker build \
	--rm \
	--build-arg "MESHROOM_VERSION=${MESHROOM_VERSION}" \
	--build-arg "CUDA_VERSION=${CUDA_VERSION}" \
	--build-arg "UBUNTU_VERSION=${UBUNTU_VERSION}" \
	--build-arg "AV_VERSION=${AV_VERSION}" \
	--tag "alicevision/meshroom:${MESHROOM_VERSION}-av${AV_VERSION}-ubuntu${UBUNTU_VERSION}-cuda${CUDA_VERSION}" \
	-f docker/Dockerfile_ubuntu .

