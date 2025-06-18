#!/bin/bash
set -ex

test -z "$MESHROOM_VERSION" && MESHROOM_VERSION="$(git rev-parse --abbrev-ref HEAD)-$(git rev-parse --short HEAD)"
test -z "$AV_VERSION" && echo "AliceVision version not specified, set AV_VERSION in the environment" && exit 1
test -z "$CUDA_VERSION" && CUDA_VERSION="12.1.0"
test -z "$UBUNTU_VERSION" && UBUNTU_VERSION="22.04"

test -d docker || (
	echo This script must be run from the top level Meshroom directory
	exit 1
)

VERSION_NAME=${MESHROOM_VERSION}-av${AV_VERSION}-ubuntu${UBUNTU_VERSION}-cuda${CUDA_VERSION}

# Retrieve the Meshroom bundle folder
rm -rf ./Meshroom-${VERSION_NAME}
CID=$(docker create alicevision/meshroom:${VERSION_NAME})
docker cp ${CID}:/opt/Meshroom_bundle ./Meshroom-${VERSION_NAME}
docker rm ${CID}

