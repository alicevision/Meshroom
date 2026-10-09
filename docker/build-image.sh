#!/usr/bin/env bash
set -euo pipefail

# Build the Meshroom dependencies image on top of the AliceVision image, then the Meshroom image.
# Shared by build-rocky.sh and build-ubuntu.sh; see docker/common.sh for the environment variables.

. docker/common.sh

docker/download-models.sh

"$CONTAINER_ENGINE" build \
    --rm \
    --progress=plain \
    --build-arg "AV_IMAGE=${AV_IMAGE}" \
    --tag "${DEPS_IMAGE}" \
    -f "docker/Dockerfile_${OS}_deps" .

"$CONTAINER_ENGINE" build \
    --rm \
    --progress=plain \
    --build-arg "DEPS_IMAGE=${DEPS_IMAGE}" \
    --tag "${IMAGE}" \
    -f docker/Dockerfile .
