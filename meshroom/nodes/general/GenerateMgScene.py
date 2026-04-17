# -*- coding: utf-8 -*-

__version__ = "1.1"

import shutil
import shlex
import logging
import subprocess
from pathlib import Path

import meshroom
from meshroom.core import desc


_MESHROOM_ROOT = Path(meshroom.__file__).parent.parent.as_posix()
_MESHROOM_BATCH = (Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch").as_posix()
PYTHON_EXE = "python"


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
        templateScene = node.templatePath.getValueStr()
        inputOverrides = self.get_overrides(node.inputOverrides)
        paramOverrides = self.get_overrides(node.paramOverrides)
        sceneDestination = node.sceneDestination.getValueStr()
        if node.sceneDestination.getValueStr():
            sceneDestination = Path(sceneDestination)
        else:
            sceneDestination = Path(node.internalFolder.value) / "scene.mg"
        
        logging.info(f"Using template scene : {templateScene}")
        if paramOverrides:
            logging.info("=== Scene overrides ===")
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
        overrides = [f"{k}='{v}'" for k, v in paramOverrides.items()]
        if overrides:
            command += f" --paramOverrides {' '.join(overrides)}"
        command += " --compute no"
        
        if invalidationString:=node.setInvalidationString.value:
            command += " --setInvalidationString " + invalidationString

        # Launch subprocess
        logging.info(f"Executing command {command}")
        subprocess.call(shlex.split(command))
        
        # Set output value
        node.meshroomScene.value = str(sceneDestination)
