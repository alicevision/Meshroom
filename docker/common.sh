# shellcheck shell=bash
# Common setup sourced by build-image.sh and extract-image.sh: container engine and image tags.
#
# Required environment:
#   OS          rocky | ubuntu
#   OS_VERSION  e.g. 9 (rocky) or 22.04 (ubuntu)
#   AV_VERSION  tag of the AliceVision image to build on
# Optional overrides:
#   CUDA_VERSION      (default 12.8.0)
#   MESHROOM_VERSION  (default: <branch>-<short-sha>)
#   CONTAINER_ENGINE  docker | podman (default: podman if available, docker otherwise)

: "${OS:?OS must be set (rocky|ubuntu)}"
: "${OS_VERSION:?OS_VERSION must be set}"
: "${AV_VERSION:?AliceVision version not specified, set AV_VERSION in the environment}"
: "${CUDA_VERSION:=12.8.0}"

test -e "docker/Dockerfile_${OS}_deps" || {
    echo "This script must be run from the top level Meshroom directory" >&2
    exit 1
}

if [[ -z "${MESHROOM_VERSION:-}" ]]; then
    # '/' (e.g. in "fix/..." branch names) is invalid in an image tag
    branch=$(git rev-parse --abbrev-ref HEAD)
    MESHROOM_VERSION="${branch//\//-}-$(git rev-parse --short HEAD)"
fi

# podman first: it often comes with a "docker" alias, which would hide it
if [[ -z "${CONTAINER_ENGINE:-}" ]]; then
    if command -v podman >/dev/null 2>&1; then
        CONTAINER_ENGINE=podman
    elif command -v docker >/dev/null 2>&1; then
        CONTAINER_ENGINE=docker
    else
        echo "No container engine found: install docker or podman, or set CONTAINER_ENGINE." >&2
        exit 1
    fi
fi
if [[ "$CONTAINER_ENGINE" = "docker" ]]; then
    # BuildKit is needed for the RUN --mount options of the Dockerfiles
    export DOCKER_BUILDKIT=1
else
    # buildah defaults to the OCI image format, which drops the SHELL instruction
    export BUILDAH_FORMAT=docker
fi

VERSION_NAME="${MESHROOM_VERSION}-av${AV_VERSION}-${OS}${OS_VERSION}-cuda${CUDA_VERSION}"
AV_IMAGE="alicevision/alicevision:${AV_VERSION}-${OS}${OS_VERSION}-cuda${CUDA_VERSION}"
DEPS_IMAGE="alicevision/meshroom-deps:${VERSION_NAME}"
IMAGE="alicevision/meshroom:${VERSION_NAME}"

echo "CONTAINER_ENGINE: ${CONTAINER_ENGINE}"
echo "IMAGE:            ${IMAGE}"
