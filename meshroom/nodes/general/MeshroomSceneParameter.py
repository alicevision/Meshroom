# -*- coding: utf-8 -*-

__version__ = "1.0"

from meshroom.core import desc


class MeshroomSceneParameter(desc.Node):
    """ Build a parameter/input override.

There are 2 modes of overrides:
- **node_instance** mode (`NODEINSTANCE.param=value`): only one node instance (identified by its name) is overridden
- **node_type** mode (`NODETYPE:param=value`): all nodes of the given type are overridden
    """

    category = "Utils"

    inputs = [
        desc.StringParam(
            name="nodeName",
            label="Node",
            description="Node instance name or node type.",
            value="",
            exposed=True,
        ),
        desc.StringParam(
            name="attrName",
            label="Attribute Name",
            description="Attribute Name.",
            value="",
            exposed=True,
        ),
        desc.StringParam(
            name="attrValue",
            label="Attribute Value",
            description="Attribute Value.",
            value="",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="mode",
            label="Mode",
            description=(
                "Override modes:\n"
                "- node_instance: Override the node instance\n"
                "- node_type: Override all nodes having this type"
            ),
            value="node_instance",
            values=["node_instance", "node_type"],
        ),
    ]

    outputs = [
        desc.StringParam(
            name="output",
            label="Output",
            description="Overriding string.",
            value=None,
        )
    ]

    def process(self, node):
        nodeName = node.nodeName.value
        attrName = node.attrName.value
        attrValue = node.attrValue.value
        mode = node.mode.value
        
        if not all([nodeName, attrValue]):
            node.output.value = ""
            return

        if mode == "node_instance":
            delimiter = "."
        elif mode == "node_type":
            delimiter = ":"
        else:
            raise ValueError(f"Mode {mode} is not recognized")

        if attrName:
            node.output.value = f"{nodeName}{delimiter}{attrName}={attrValue}"
        else:
            node.output.value = f"{nodeName}={attrValue}"
