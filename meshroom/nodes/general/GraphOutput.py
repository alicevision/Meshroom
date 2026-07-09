# -*- coding: utf-8 -*-

__version__ = "1.0"

import os
import json
import logging
from pprint import pformat 
from meshroom.core import desc


class GraphOutput(desc.Node, desc.OutputNode):
    outputAttributes = ["outputFolder", "outputFile"]

    inputs = [
        desc.File(
            name="outputFolder",
            value="",
        ),
        desc.File(
            name="outputFile",
            value=None
        ),
        desc.AnySet(
            name="outputs",
            exposed=True
        )
    ]

    def setOutputFolder(self, node, outputFolder):
        node.outputFolder.value = outputFolder
        node.outputFile.value = os.path.join(node.outputFolder.value, "outputs.json")

    def process(self, node):
        outputFolder = node.outputFolder.value
        outputFile = node.outputFile.value

        if not outputFolder:
            return
        if not os.path.exists(outputFolder):
            logging.info(f"Create folder {outputFolder}")
            os.makedirs(outputFolder)

        serializedOutputs = {}
        for item in node.outputs._getValue():
            serializedOutputs[item.name] = item.value

        logging.info(f"Graph outputs:\n{pformat(serializedOutputs, indent=2)}")
        with open(outputFile, "w") as f:
            json.dump(serializedOutputs, f, indent=4)

        logging.info(f"Saved outputs inside {outputFile}")
