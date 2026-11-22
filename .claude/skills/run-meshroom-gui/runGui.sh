#!/bin/bash
# Run driveMeshroom.py in its own process group, offscreen, with a hard timeout,
# and kill whatever is left of that group when it ends or is interrupted.
#
# Usage: runGui.sh [-t TIMEOUT_SECONDS] [-v] [-l LOGFILE] [DRIVER_ARGS...]
#   -v  show the window on $DISPLAY instead of running offscreen
# Env:
#   MESHROOM_ENV_CMD  command prefix providing the Python environment, e.g. "rez env meshroom --"
#   MESHROOM_PYTHON   Python interpreter (default: python3)

SKILL_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
MESHROOM_ROOT="$(readlink -f "$SKILL_DIR/../../..")"
TIMEOUT=240
VISIBLE=0
LOG=/dev/stdout

# Parse launcher options until the first other argument: the rest goes to the driver (e.g. --scenario)
while [ $# -gt 0 ]; do
    case $1 in
        -t) TIMEOUT=$2; shift 2 ;;
        -v) VISIBLE=1; shift ;;
        -l) LOG=$2; shift 2 ;;
        --) shift; break ;;
        *) break ;;
    esac
done

[ "$VISIBLE" = 1 ] || export QT_QPA_PLATFORM=offscreen
export MESHROOM_ROOT
PYTHON="${MESHROOM_PYTHON:-python3}"

# Quote the driver command so it survives the optional environment prefix
DRIVER="PYTHONPATH=$(printf %q "$MESHROOM_ROOT"):\$PYTHONPATH exec $PYTHON $(printf %q "$SKILL_DIR/driveMeshroom.py")"
for a in "$@"; do DRIVER+=" $(printf %q "$a")"; done

# Backgrounded, setsid execs in place: its PID is the process group ID of the whole run
setsid timeout -k 10 "$TIMEOUT" $MESHROOM_ENV_CMD bash -c "$DRIVER" > "$LOG" 2>&1 &
PGID=$!

cleanup() {
    kill -KILL -- -"$PGID" 2>/dev/null
}
trap 'cleanup; exit 130' INT TERM

wait "$PGID"
STATUS=$?
cleanup
if pgrep -g "$PGID" > /dev/null 2>&1; then
    echo "runGui.sh: processes still alive in group $PGID" >&2
    STATUS=1
fi
echo "runGui.sh: exit status $STATUS" >&2
exit $STATUS
