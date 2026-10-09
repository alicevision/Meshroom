#!/usr/bin/env bash
set -euo pipefail

# Extract the Meshroom bundle from the Meshroom image into ./Meshroom-<version>.
# Shared by extract-rocky.sh and extract-ubuntu.sh; see docker/common.sh for the environment variables.

. docker/common.sh

DEST="./Meshroom-${VERSION_NAME}"
rm -rf "${DEST}"

CID=$("$CONTAINER_ENGINE" create "${IMAGE}")
trap '"$CONTAINER_ENGINE" rm "${CID}" >/dev/null' EXIT

"$CONTAINER_ENGINE" cp "${CID}:/opt/Meshroom_bundle" "${DEST}"

# Images shipping a standalone Python runtime (/opt/python, used to run Python nodes):
# retrieve it completely, including licenses and metadata
if "$CONTAINER_ENGINE" run --rm --entrypoint test "${IMAGE}" -d /opt/python; then
    mkdir -p "${DEST}/python"
    "$CONTAINER_ENGINE" cp "${CID}:/opt/python/." "${DEST}/python/"
fi
