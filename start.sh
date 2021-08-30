#!/bin/bash
export MESHROOM_ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}" )" )"
export PYTHONPATH=$MESHROOM_ROOT:$PYTHONPATH

# using existing alicevision release
#export LD_LIBRARY_PATH=/foo/Meshroom-2021.1.0/aliceVision/lib/
#export PATH=$PATH:/foo/Meshroom-2021.1.0/aliceVision/bin/

# using alicevision built source
#export PATH=$PATH:/foo/build/Linux-x86_64/

python "$MESHROOM_ROOT/meshroom/ui"
