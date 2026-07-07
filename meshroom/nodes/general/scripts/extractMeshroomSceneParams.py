# -*- coding: utf-8 -*-

"""
This script will:
- Load a Meshroom scene.
- Extract requested parameters from nodes.
- Write the result of requested parameters on a JSON file.
"""

import sys
import json
import logging
import argparse
from pathlib import Path

from meshroom.core.graph import loadGraph


REQUEST_SEPARATOR = ";"
NODE_PARAM_SEPARATOR = ":"


parser = argparse.ArgumentParser(
    description="Extract parameter values from a Meshroom scene."
)
parser.add_argument("--scene", required=True,
    help="Path to the source Meshroom scene (.mg) to read parameters from.",
)
parser.add_argument("--request", required=True,
    help=(
        "List of 'nodeInstance:param' pairs, separated by semicolon. "
        "(e.g. 'MyNode_1:paramName;MyNode_2:groupParam.parameter')."
    )
)
parser.add_argument("--output", required=True, help="Output JSON file.")

args = parser.parse_args()

# Get scene
scenePath = Path(args.scene)
if not scenePath.exists():
    logging.error(f"Scene does not exist: {scenePath}")
    sys.exit(1)

# Get output JSON
outputFile = Path(args.output)
if not outputFile.parent.exists():
    outputFile.parent.mkdir(parents=True, exist_ok=True)

# Get requested parameters
requestedParams = []
for item in args.request.split(REQUEST_SEPARATOR):
    item = item.strip()
    if not item:
        continue
    if NODE_PARAM_SEPARATOR not in item:
        raise ValueError(
            f"Invalid request '{item}': expected 'nodeInstance{NODE_PARAM_SEPARATOR}param'."
        )
    nodeName, paramPath = item.split(NODE_PARAM_SEPARATOR)
    if not nodeName or not paramPath:
        raise ValueError(f"Invalid request '{item}': empty node name or param path.")
    requestedParams.append((nodeName, paramPath))
if not requestedParams:
    logging.error(f"No parameters to get: {args.request}")
    sys.exit(1)

# Print infos
logging.info("[Extract Meshroom Scene Parameters]")
logging.info(f"  input scene: {scenePath}")
logging.info(f"  output file: {outputFile}")
logging.info("  parameters:")
for n, p in requestedParams:
    logging.info(f"  - {n} -> {p}")

# Open the node graph
logging.info(f"Loading scene: {scenePath}")
graph = loadGraph(str(scenePath))

# Extract parameters
parameters = []
for nodeInstance, paramPath in requestedParams:
    try:
        node = graph.node(nodeInstance)
    except Exception as e:
        raise RuntimeError(f"Node '{nodeInstance}' not found in scene.\n") from e

    if node is None:
        raise RuntimeError(f"Node '{nodeInstance}' not found in scene.")
    
    if not node.hasAttribute(paramPath):
        raise RuntimeError(f"Attribute '{paramPath}' not found on node '{nodeInstance}'.")

    attr = node.attribute(paramPath)
    value = attr.getValueStr(withQuotes=False)
    parameters.append({
        "node": nodeInstance,
        "parameter": paramPath,
        "value": value,
    })
    logging.info(f"Extracted parameter: {nodeInstance}.{paramPath} -> '{value}")

# Export in the output file
with open(outputFile, "w") as f:
    json.dump(parameters, f, indent=2)

logging.info(f"Exported result to {outputFile}")
