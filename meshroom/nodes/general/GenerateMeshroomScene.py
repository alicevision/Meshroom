# -*- coding: utf-8 -*-

__version__ = "1.0"

import shlex
import logging
import subprocess
from pathlib import Path

import meshroom
from meshroom import _MESHROOM_ROOT
from meshroom.core import desc


_MESHROOM_BATCH = Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch"


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
            label="Parameter overrides",
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
            raise ValueError(f"{node} Invalid template scene: {templateScene}")
        inputOverrides = self.get_overrides(node.inputOverrides)
        paramOverrides = self.get_overrides(node.paramOverrides)
        sceneDestination = str(node.sceneDestination.getValueStr(withQuotes=False))
        if sceneDestination:
            sceneDestination = Path(sceneDestination)
        else:
            sceneDestination = Path(node.internalFolder) / "scene.mg"

        logging.info(f"- Using template scene: {templateScene}")
        logging.info(f"- Scene destination: {sceneDestination}")

        if inputOverrides or paramOverrides:
            logging.info(f"{'='*10} Scene overrides {'='*10}")
            for item in inputOverrides:
                logging.info(f"- Override input: {item}")
            for item in paramOverrides:
                logging.info(f"- Override parameter: {item}")

        sceneRoot = sceneDestination.parent
        if not sceneRoot.exists():
            logging.info(f"Creating parent folder: {sceneRoot}")
            sceneRoot.mkdir(parents=True, exist_ok=True)

        command = [self.pythonExecutable, str(_MESHROOM_BATCH), "-p", templateScene]
        command += ["-p", templateScene]
        if inputOverrides:
            command += ["--input"] + inputOverrides
        command += ["--save", str(sceneDestination)]
        if paramOverrides:
            command += ["--paramOverrides"] + paramOverrides
        command += ["--compute", "no"]
        if invalidationString := node.setInvalidationString.value:
            command += ["--setInvalidationString", invalidationString]
        
        # Launch subprocess
        logging.info(f"{'='*10} Command {'='*10}")
        logging.info(f"{shlex.join(command)}")
        logging.info(f"{'='*10} Subprocess output {'='*10}")
        out = subprocess.call(command)    
        if out:
            raise RuntimeError(f"Node {node} failed")

        # Set output value
        node.meshroomScene.value = str(sceneDestination)
