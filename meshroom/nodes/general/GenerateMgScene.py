# -*- coding: utf-8 -*-

__version__ = "1.1"

import shlex
import logging
import subprocess
from pathlib import Path

import meshroom
from meshroom.core import desc


_MESHROOM_ROOT = Path(meshroom.__file__).parent.parent.as_posix()
_MESHROOM_BATCH = (Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch").as_posix()
PYTHON_EXE = "python"



class MeshroomSceneParameter(desc.Node):
    """ Build a parameter/input override.

There are 2 modes of overrides :
- **node_instance** mode (`NODEINSTANCE.param=value`) : only one node instance is overriden
- **node_type** mode (`NODETYPE:param=value`) : all nodes of the type are overrided
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
            name="paramName",
            label="Parameter",
            description="Parameter name",
            value="",
            exposed=True,
        ),
        desc.StringParam(
            name="paramValue",
            label="Value",
            description="",
            value="",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="mode",
            label="Mode",
            description=(
                "Override modes :\n"
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
        paramName = node.paramName.value
        paramValue = node.paramValue.value
        mode = node.mode.value
        
        if not all([nodeName, paramValue]):
            node.output.value = ""
            return

        delimiter = ":"
        if mode == "node_instance":
            delimiter = "."
        elif mode == "node_type":
            delimiter = ":"
        else:
            raise ValueError(f"Mode {mode} is not recognized")

        if paramName:
            node.output.value = f"{nodeName}{delimiter}{paramName}={paramValue}"
        else:
            node.output.value = f"{nodeName}={paramValue}"


class GenerateMeshroomScene(desc.Node):
    """
    Generate a Meshroom camera tracking project and launch its computation.
    """

    category = "Utils"

    inputs = [
        desc.File(
            name="templatePath",
            label="Template",
            description="Meshroom template scene.",
            value="",
            exposed=True
        ),
        desc.File(
            name="sceneDestination",
            label="Scene Path",
            description="Save the scene to this destination. If empty, will be saved on the cache folder",
            value="",
            exposed=True
        ),
        desc.ListAttribute(
            name="inputOverrides",
            label="Input Overrides",
            description="Overrides for the CameraInit nodes.",
            exposed=True,
            commandLineGroup="",
            elementDesc=desc.StringParam(
                name="inputOverride",
                label="Input Override",
                description="Override string on the format <nodeName>:<images path>.",
                commandLineGroup=None,
                exposed=True,
                value=""
            )
        ),
        desc.ListAttribute(
            name="paramOverrides",
            label="Parameters overrides",
            description="Overrides for the nodes in the Meshroom scene to create.",
            exposed=True,
            commandLineGroup="",
            elementDesc=desc.StringParam(
                name="paramOverride",
                label="Override",
                description="Key/Value override.",
                commandLineGroup=None,
                exposed=True,
                value=""
            )
        ),
        desc.StringParam(
            name="setInvalidationString",
            label="Invalidation String",
            description="Set an invalidation string on the scene nodes.",
            value="",
            exposed=False
        ),
    ]

    outputs = [
        desc.File(
            name="meshroomScene",
            label="Meshroom Scene",
            description="Meshroom Scene.",
            value=None,
        )
    ]

    @staticmethod
    def get_overrides(listParam):
        overrides = []
        overridesList = listParam.value
        for override in overridesList:
            overrideValue = override.value
            if overrideValue:
                overrides.append(overrideValue)
        return overrides

    def process(self, node):
        templateScene = node.templatePath.getValueStr(withQuotes=False)
        if not templateScene or not Path(templateScene).exists():
            raise ValueError(f"{node} Invalid template scene : {templateScene}")
        inputOverrides = self.get_overrides(node.inputOverrides)
        paramOverrides = self.get_overrides(node.paramOverrides)
        sceneDestination = str(node.sceneDestination.getValueStr(withQuotes=False))
        if sceneDestination:
            sceneDestination = Path(sceneDestination)
        else:
            sceneDestination = Path(node.internalFolder) / "scene.mg"

        logging.info(f"- Using template scene : {templateScene}")
        logging.info(f"- Scene destination : {sceneDestination}")

        if inputOverrides or paramOverrides:
            logging.info(f"{'='*10} Scene overrides {'='*10}")
            for item in inputOverrides:
                logging.info(f"- Override input : {item}")
            for item in paramOverrides:
                logging.info(f"- Override parameter : {item}")

        sceneRoot = sceneDestination.parent
        if not sceneRoot.exists():
            logging.info(f"Creating parent folder : {sceneRoot}")
            sceneRoot.mkdir(parents=True, exist_ok=True)

        # Build command
        command  = f"{PYTHON_EXE} {_MESHROOM_BATCH}"
        command += f" -p {templateScene}"
        if inputOverrides:
            command += f" --input {' '.join(inputOverrides)}"
        command += f" --save {str(sceneDestination)}"
        # Add overrides
        if paramOverrides:
            command += f" --paramOverrides {' '.join(paramOverrides)}"
        command += " --compute no"

        if invalidationString:=node.setInvalidationString.value:
            command += " --setInvalidationString " + invalidationString

        # Launch subprocess
        logging.info(f"{'='*10} Command {'='*10}")
        logging.info(f"{command}")

        logging.info(f"{'='*10} Subprocess output {'='*10}")
        out = subprocess.call(shlex.split(command))
        if out:
            raise RuntimeError(f"Node {node} failed")

        # Set output value
        node.meshroomScene.value = str(sceneDestination)
