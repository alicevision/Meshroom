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


def getRequestedParams(request) -> tuple[str, str]:
    """ Parse the request argument and extract a list of (nodeInstance, paramPath). """
    # Get requested parameters
    requestedParams = []
    for item in request.split(REQUEST_SEPARATOR):
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
    return requestedParams


def openGraph(scene):
    """ Open the node graph. """
    logging.info(f"Loading scene: {scene}")
    graph = loadGraph(str(scene))
    return graph


def extractParameters(graph, requestedParams, failOnMissingParams=True):
    """ Extract requested parameters from the graph. """
    parameters = []
    missingParams = []
    for nodeInstance, paramPath in requestedParams:
        node = graph.node(nodeInstance)
        if node is None:
            logging.warning(f"Node {nodeInstance} is not in the scene.")
            missingParams.append(f"{nodeInstance}.{paramPath}")
            continue
        if not node.hasAttribute(paramPath):
            logging.warning(f"Node {nodeInstance} has no attribute {paramPath}.")
            missingParams.append(f"{nodeInstance}.{paramPath}")
            continue

        attr = node.attribute(paramPath)
        value = attr.getValueStr(withQuotes=False)
        parameters.append({
            "node": nodeInstance,
            "parameter": paramPath,
            "value": value,
        })
        logging.info(f"Parameter: {nodeInstance}.{paramPath}='{value}'")
    if missingParams and failOnMissingParams:
        raise RuntimeError(f"Missing parameters {missingParams} from scene graph.")
    return parameters


def exportJson(outputPath, content):
    outputFile = Path(outputPath)
    if not outputFile.parent.exists():
        logging.info(f"Create folder: {outputFile.parent}")
        outputFile.parent.mkdir(parents=True, exist_ok=True)

    # Export in the output file
    with open(outputFile, "w") as f:
        json.dump(content, f, indent=2)

    logging.info(f"Exported result to {outputFile}")


def main(args):
    # Get scene
    scenePath = Path(args.scene)
    if not scenePath.exists():
        logging.error(f"Scene does not exist: {scenePath}")
        if args.failOnMissingScene:
            sys.exit(1)
        else:
            exportJson(args.output, {})
            sys.exit(0)

    # Get requested params
    requestedParams = getRequestedParams(request=args.request)

    # Print infos
    logging.info("[Extract Meshroom Scene Parameters]")
    logging.info(f"  input scene: {scenePath}")
    logging.info(f"  output file: {args.output}")
    logging.info("  parameters:")
    for n, p in requestedParams:
        logging.info(f"  - {n} -> {p}")

    # Open the graph
    graph = openGraph(scenePath)

    # Extract params
    parameters = extractParameters(
        graph, requestedParams, failOnMissingParams=args.failOnMissingParams
    )

    # Export to the output
    exportJson(args.output, content=parameters)


if __name__ == "__main__":
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

    parser.add_argument(
        "--failOnMissingScene", action="store_true",
        help="Fail if the scene doesn't exist."
    )
    parser.add_argument(
        "--failOnMissingParams", action="store_true",
        help="FaiFail if we don't find one or several params inside the scene."
    )

    args = parser.parse_args()
    
    main(args)
