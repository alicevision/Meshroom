#!/bin/sh
export PYTHONPATH="$(dirname "$(readlink -f "${BASH_SOURCE[0]}" )" )"
python meshroom/ui
