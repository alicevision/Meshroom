#!/bin/bash
export MESHROOM_ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}" )" )"
export PYTHONPATH=$MESHROOM_ROOT:$PYTHONPATH

# Activate virtual environment if it exists
if [ -d "$MESHROOM_ROOT/meshroom_venv" ]; then
    source "$MESHROOM_ROOT/meshroom_venv/bin/activate"
fi

# Using AliceVision from prebuilt Meshroom installation
MESHROOM_PREBUILT="/home/haaken/Nedlastinger/Meshroom-2023.3.0"
if [ -d "$MESHROOM_PREBUILT/aliceVision" ]; then
    export ALICEVISION_ROOT="$MESHROOM_PREBUILT/aliceVision"
    export LD_LIBRARY_PATH="$ALICEVISION_ROOT/lib:$LD_LIBRARY_PATH"
    export PATH="$ALICEVISION_ROOT/bin:$PATH"
    # Only set these if the directories exist
    if [ -d "$ALICEVISION_ROOT/share/meshroom" ]; then
        export MESHROOM_NODES_PATH="$ALICEVISION_ROOT/share/meshroom"
        export MESHROOM_PIPELINE_TEMPLATES_PATH="$ALICEVISION_ROOT/share/meshroom"
    fi
    echo "Using AliceVision from: $ALICEVISION_ROOT"
fi

# Set plugin path for MrIMU
export MESHROOM_PLUGINS_PATH="$MESHROOM_ROOT/plugins/MrIMU:$MESHROOM_PLUGINS_PATH"

python3 "$MESHROOM_ROOT/meshroom/ui"
