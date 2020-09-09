#!/bin/bash
set -ex

AV_VERSION="2.2.10.hdri"
MESHROOM_VERSION="2020.0.1.hdri"

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

VERSION_NAME=${MESHROOM_VERSION}-av${AV_VERSION}-centos${CENTOS_VERSION}-cuda${CUDA_VERSION}${PYTHON2_DOCKER_EXT}

# Retrieve the Meshroom bundle folder
rm -rf ./Meshroom-${VERSION_NAME}
CID=$(docker create alicevision/meshroom:${VERSION_NAME})
docker cp ${CID}:/opt/Meshroom_bundle ./Meshroom-${VERSION_NAME}
docker rm ${CID}

