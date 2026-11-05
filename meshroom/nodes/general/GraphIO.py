__version__ = "1.0"

import json
import logging
import os
from pprint import pformat

from meshroom.core import desc
from meshroom.core.attribute import GroupAttribute, ListAttribute


DEFAULT_OUTPUT_FILENAME = "outputs.json"


def attributeToJson(attribute):
    """
    Convert an attribute value into JSON-serializable data, following links.

    Args:
        attribute (Attribute): the attribute to convert

    Returns:
        the attribute value, with lists and groups converted to Python lists and dicts
    """
    if isinstance(attribute, ListAttribute):
        return [attributeToJson(child) for child in attribute.value]
    if isinstance(attribute, GroupAttribute):
        return {child.name: attributeToJson(child) for child in attribute.value}
    return attribute.value


class GraphInput(desc.InitNode, desc.InputNode):
    """
    Expose attributes as the inputs of the scene.
    When the scene is computed by another graph (e.g. with ComputeMeshroomScene), these attributes can be set from it.

    Connect the "Exposed attributes" pin to the input attributes of other nodes to create one graph input per connection.
    Its attributes are the entry points of the graph: they cannot be connected as destination.
    """

    def __init_subclass__(cls, **kwargs):
        # Standard node identifying the inputs of a graph by its node type
        raise TypeError(f"'{cls.__name__}': GraphInput is a standard Meshroom node and cannot be subclassed.")

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
            description="Attributes exposed as the inputs of the scene.",
            exposed=True
        )
    ]


class GraphOutput(desc.Node):
    """
    Expose attributes as the outputs of the scene.
    When the scene is computed by another graph (e.g. with ComputeMeshroomScene), these attributes can be read from it.
    They are exported into a JSON file if an output folder or file is set, for instance with
    `meshroom_batch --graphOutput FOLDER`.

    Not an OutputNode, as output nodes are removed from the graphs created from a template.
    """

    def __init_subclass__(cls, **kwargs):
        # Standard node identifying the outputs of a graph by its node type
        raise TypeError(f"'{cls.__name__}': GraphOutput is a standard Meshroom node and cannot be subclassed.")

    category = "Utils"

    inputs = [
        desc.File(
            name="outputFolder",
            label="Output Folder",
            description="Folder in which the graph outputs are exported.",
            value="",
        ),
        desc.File(
            name="outputFile",
            label="Output File",
            description=f"JSON file in which the graph outputs are exported.\n"
                        f"If empty, '{DEFAULT_OUTPUT_FILENAME}' is written in the output folder.",
            value="",
        ),
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
            description="Attributes exposed as the outputs of the scene.",
            exposed=True
        )
    ]

    def getOutputFilePath(self, node):
        """
        Returns:
            str: the path of the JSON file to write, or an empty string if neither the file nor the folder is set
        """
        if node.outputFile.value:
            return node.outputFile.value
        if node.outputFolder.value:
            return os.path.join(node.outputFolder.value, DEFAULT_OUTPUT_FILENAME)
        return ""

    def process(self, node):
        outputFile = self.getOutputFilePath(node)
        if not outputFile:
            logging.info(f"[{node.name}] No output folder or file set: graph outputs are not exported.")
            return

        outputFolder = os.path.dirname(outputFile)
        if outputFolder:
            os.makedirs(outputFolder, exist_ok=True)

        serializedOutputs = {attr.name: attributeToJson(attr) for attr in node.exposeds.value}

        logging.info(f"Graph outputs:\n{pformat(serializedOutputs, indent=2)}")
        with open(outputFile, "w") as f:
            json.dump(serializedOutputs, f, indent=4)

        logging.info(f"Saved outputs inside {outputFile}")
