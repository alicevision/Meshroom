#!/bin/bash

source /home/wp13/RI-IML-RTVFX/FastMatch/bash_profile

BINARY=$1
NODENAME=$2
MESHROOMFILE=$3
COUNT_CORES=$4

THREAD_ID=$((${SLURM_ARRAY_TASK_ID} - 1))

export OMP_NUM_THREADS=$4

echo "${BINARY} --node ${NODENAME} "${MESHROOMFILE}" --iteration ${THREAD_ID} --extern" 

${BINARY} --node ${NODENAME} "${MESHROOMFILE}" --iteration ${THREAD_ID} --extern