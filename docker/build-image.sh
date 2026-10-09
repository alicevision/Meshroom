#!/usr/bin/env bash
set -euo pipefail

# Build the Meshroom dependencies image on top of the AliceVision image, then the Meshroom image.
# Shared by build-rocky.sh and build-ubuntu.sh; see docker/common.sh for the environment variables.

. docker/common.sh

docker/download-models.sh

OS_VERSION_ARG="$(echo "$OS" | tr '[:lower:]' '[:upper:]')_VERSION=${OS_VERSION}"

"$CONTAINER_ENGINE" build \
    --rm \
    --progress=plain \
    --build-arg "CUDA_VERSION=${CUDA_VERSION}" \
    --build-arg "${OS_VERSION_ARG}" \
    --build-arg "AV_VERSION=${AV_VERSION}" \
    --tag "${DEPS_IMAGE}" \
    -f "docker/Dockerfile_${OS}_deps" .

"$CONTAINER_ENGINE" build \
    --rm \
    --progress=plain \
    --build-arg "MESHROOM_VERSION=${MESHROOM_VERSION}" \
    --build-arg "CUDA_VERSION=${CUDA_VERSION}" \
    --build-arg "${OS_VERSION_ARG}" \
    --build-arg "AV_VERSION=${AV_VERSION}" \
    --tag "${IMAGE}" \
    -f "docker/Dockerfile_${OS}" .
