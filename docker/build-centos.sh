#!/bin/bash
set -ex


test -z "$MESHROOM_VERSION" && MESHROOM_VERSION="$(git rev-parse --abbrev-ref HEAD)-$(git rev-parse --short HEAD)"
test -z "$AV_VERSION" && echo "AliceVision version not specified, set AV_VERSION in the environment" && exit 1
test -z "$CUDA_VERSION" && CUDA_VERSION="10.2"
test -z "$CENTOS_VERSION" && CENTOS_VERSION="7"
test -z "$MESHROOM_PYTHON2" || echo "========== Build for Python 2 =========="
test -z "$MESHROOM_PYTHON2" || export PYTHON2_DOCKER_EXT="-py2"
test -z "$MESHROOM_PYTHON2" || export PYTHON2_DOCKERFILE_EXT="_py2"
test -z "$MESHROOM_PYTHON2" && echo "========== Build for Python 3 =========="

test -d docker || (
	echo This script must be run from the top level Meshroom directory
	exit 1
)

test -d dl || \
        mkdir dl
test -f dl/qt.run || \
        wget "https://download.qt.io/archive/qt/5.14/5.14.1/qt-opensource-linux-x64-5.14.1.run" -O "dl/qt.run"

# DEPENDENCIES
docker build \
	--rm \
	--build-arg "CUDA_VERSION=${CUDA_VERSION}" \
	--build-arg "CENTOS_VERSION=${CENTOS_VERSION}" \
	--build-arg "AV_VERSION=${AV_VERSION}" \
	--tag "alicevision/meshroom-deps:${MESHROOM_VERSION}-av${AV_VERSION}-centos${CENTOS_VERSION}-cuda${CUDA_VERSION}${PYTHON2_DOCKER_EXT}" \
	-f docker/Dockerfile_centos_deps${PYTHON2_DOCKERFILE_EXT} .

# Meshroom
docker build \
	--rm \
	--build-arg "MESHROOM_VERSION=${MESHROOM_VERSION}" \
	--build-arg "CUDA_VERSION=${CUDA_VERSION}" \
	--build-arg "CENTOS_VERSION=${CENTOS_VERSION}" \
	--build-arg "AV_VERSION=${AV_VERSION}" \
	--tag "alicevision/meshroom:${MESHROOM_VERSION}-av${AV_VERSION}-centos${CENTOS_VERSION}-cuda${CUDA_VERSION}${PYTHON2_DOCKER_EXT}" \
	-f docker/Dockerfile_centos${PYTHON2_DOCKERFILE_EXT} .

