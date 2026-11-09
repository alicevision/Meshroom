# -*- coding: utf-8 -*-

__version__ = "2.0"

import os
import re
import shlex
from pathlib import Path
from typing import Callable, List, Tuple

from meshroom.core.attribute import AnySet, Attribute, GroupAttribute, ListAttribute
from meshroom.core.desc.validators import success
from meshroom.core.desc.validators import error
from meshroom.core.exception import InvalidEdgeError
from meshroom.core.graph import loadGraph
from meshroom.core import desc

from meshroom import _MESHROOM_ROOT

import logging


logger = logging.getLogger(__name__)


_MESHROOM_BATCH = Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch"


def isValidSceneFileValidator(node, _) -> Tuple[bool, List[str]]:
    filePath = Path(node.scene.value)
    errorMessages = []
    if not filePath.exists():
        errorMessages.append(f"{filePath} does not exist")
    if filePath.suffix not in ('.mg', '.mgt'):
        errorMessages.append(f"{filePath} should be a .mg or .mgt file")

    if len(errorMessages) > 0:
        return error(*errorMessages)

    return success()


def flattenAttributes(attributes: list[Attribute], filter: Callable = None) -> list[Attribute]:
    """
    Return the attributes that can be set individually from the command line: groups (and AnySets)
    are replaced by their children, and lists, which cannot be overridden, are skipped.

    Args:
        attributes: the attributes to flatten.
        filter: if set, the attributes (and groups) for which it returns True are skipped.
    """
    attrs = []
    for attr in attributes:
        if filter and filter(attr):
            continue

        if isinstance(attr, GroupAttribute):
            attrs += flattenAttributes(list(attr.value.values()), filter)
        elif not isinstance(attr, ListAttribute):
            attrs.append(attr)

    return attrs


def encodeAttributeName(fullName: str) -> str:
    """
    Convert the full name of a scene attribute ("Node.group.attribute") into a valid child attribute name.
    Underscores are escaped so that decodeAttributeName() can always restore the full name.
    """
    return fullName.replace("_", "_0").replace(".", "__")


def decodeAttributeName(name: str) -> str:
    """ Return the full name of the scene attribute that a child attribute was named after with encodeAttributeName(). """
    return re.sub(r"__|_0", lambda match: "." if match.group() == "__" else "_", name)


def resolvedValue(attr: Attribute):
    """ Return the value of a scene attribute, evaluated on the attribute it is linked to if any. """
    if attr.isLink:
        attr = attr._getInputLink(recursive=True)
    return attr.evalValue


def overrideValue(attr: Attribute) -> str:
    """ Return the value of an attribute as expected by meshroom_batch --paramOverrides. """
    value = attr.value
    # Non-exclusive choices are given as comma-separated values
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


class ComputeMeshroomScene(desc.CommandLineNode):
    """
    Compute or Submits a meshroom scene on the farm.
    """

    pythonExecutable = "python"
    category = "Utils"
    commandLine = "{node.nodeDesc.pythonExecutable} " + shlex.quote(str(_MESHROOM_BATCH))

    def __getSubmitters():
        from meshroom.core import submitters
        submitterNames = []
        for subName, _ in submitters.items():
            submitterNames.append(subName)
        return submitterNames

    SUBMITTERS = __getSubmitters()

    @staticmethod
    def _sceneAttribute(scene, name: str):
        """ Return the attribute of 'scene' that an exposed attribute was named after, or None if it does not exist. """
        nodeName, _, attributeName = decodeAttributeName(name).partition(".")
        sceneNode = scene.node(nodeName)
        if sceneNode is None or not attributeName:
            return None
        try:
            return sceneNode.attribute(attributeName)
        except (KeyError, ValueError):
            return None

    @staticmethod
    def _computedScenePath(node) -> str:
        """ Return the path where the scene is saved before being computed, with its cache folder next to it. """
        return os.path.join(node.internalFolder, "scene.mg")

    def buildCommandLine(self, chunk) -> str:
        cmd = super().buildCommandLine(chunk)
        node = chunk.node

        # Only the inputs whose value differs from the scene are overridden
        try:
            scene = loadGraph(node.scene.value)
        except Exception as e:
            raise RuntimeError(f"Cannot read the scene '{node.scene.value}': {e}") from e
        sceneInputs = []
        for attr in flattenAttributes(node.inputs.value):
            sceneAttr = self._sceneAttribute(scene, attr.name)
            if sceneAttr is None:
                logger.warning(f"'{decodeAttributeName(attr.name)}' does not exist in the scene anymore: not overridden.")
                continue
            if overrideValue(attr) != overrideValue(sceneAttr):
                # Each argument is quoted, as the command line is split with shlex before being executed
                sceneInputs.append(shlex.quote(f"{decodeAttributeName(attr.name)}={overrideValue(attr)}"))

        # The computed scene is saved in the node's folder so that the given scene file is left untouched
        cmd += f" -p {shlex.quote(node.scene.value)} --save {shlex.quote(self._computedScenePath(node))}"

        # ForceCompute
        if node.forceCompute.value:
            cmd += " --forceCompute"

        if sceneInputs:
            cmd += " --paramOverrides " + " ".join(sceneInputs)

        # Compute or Submit
        if node.submit.value:
            cmd += " --submit"
            if node.submitter.value:
                cmd += f" --submitter {shlex.quote(node.submitter.value)}"
            if node.submitLabel.value:
                cmd += f" --submitLabel {shlex.quote(node.submitLabel.value)}"
        else:
            cmd += " --compute yes"

        return cmd

    def processChunk(self, chunk):
        super().processChunk(chunk)
        self._updateOutputs(chunk.node)

    def _updateOutputs(self, node):
        """
        Set the exposed outputs to their values in the computed scene, whose cache folder is in the node's folder.
        They are saved with the other dynamic output values once the chunk is processed.
        """
        scene = loadGraph(self._computedScenePath(node))
        for attr in node.outputs.value:
            sceneAttr = self._sceneAttribute(scene, attr.name)
            if sceneAttr is None:
                logger.warning(f"'{decodeAttributeName(attr.name)}' does not exist in the computed scene.")
                continue
            attr.value = resolvedValue(sceneAttr)

    inputs = [
        desc.File(
            name="scene",
            label="Scene",
            description="Meshroom scene.",
            value="",
            validators=[
                isValidSceneFileValidator
            ]
        ),
        desc.BoolParam(
            name="forceCompute",
            label="Force Compute",
            description=(
                "Set True to force compute. If nodes are already computed, the status will"
                "be reset to None and the cache will be deleted."
            ),
            value=True,
        ),
        desc.BoolParam(
            name="submit",
            label="Submit",
            description="Set True to submit, False to compute locally.",
            value=False,
            enabled=len(SUBMITTERS) > 0
        ),
        desc.ChoiceParam(
            name="submitter",
            label="Submitter",
            description="Select submitter. An empty string will select the default one.",
            value="",
            values=[""] + SUBMITTERS,
            enabled=lambda node: node.submit.value is True
        ),
        desc.StringParam(
            name="submitLabel",
            label="Submit Label",
            description=(
                "The label that will be set for the submitted job name.\n"
                "An empty string will set a default string: '[Meshroom] {projectName}'.\n"
                "The following strings between brackets can be used as they will be automatically replaced:\n"
                "- projectName: the name of the scene file"
            ),
            value="",
            enabled=len(SUBMITTERS) > 0
        ),
        desc.BoolParam(
            name="useOnlyGraphIONodes",
            label="Use only GraphIO nodes",
            description="When checked, only the attributes of GraphInput nodes are exposed as inputs (outputs always come "
                        "from GraphOutput nodes).",
            value=False
        ),
        desc.StringParam(
            name="exposedScene",
            label="Exposed Scene",
            description="The scene whose attributes are exposed, to remember the values set on its inputs when it changes.",
            value="",
            invalidate=False,
            visible=False
        ),
        desc.AnySet(
            name="inputs",
            label="Inputs",
            description="All the parameters exposed in the GraphInput of the given Scene file",
            exposed=True
        )
    ]

    outputs = [
        desc.AnySet(
            name="outputs",
            label="Outputs",
            description="All the parameters exposed in the GraphOutput of the given Scene file",
            exposed=True
        )
    ]

    @staticmethod
    def _clearAnySet(anySet: AnySet):
        inputAttributes = [input for input in anySet.value]
        for input in inputAttributes:
            anySet.removeAttribute(input)

    @staticmethod
    def _exposeAttributes(anySet: AnySet, attributes: list[Attribute]):
        """ Append a copy of each scene attribute to 'anySet', named after its full name in the scene. """
        for attr in attributes:
            attrDesc = attr.asDict()
            attrDesc['name'] = encodeAttributeName(attr.fullName)
            if attr.isLink:
                # A link expression refers to a node of the scene: copy the value it resolves to
                attrDesc['value'] = resolvedValue(attr)
            anySet.insertAttribute(attrDesc, anySet.value.count)

    @staticmethod
    def _disconnectExposedAttributes(node) -> list:
        """
        Remove the edges connected to the exposed attributes, which would be left dangling once they are removed.

        Returns:
            list: the removed edges, as (source, destination) attribute full names.
        """
        if node.graph is None:
            return []
        exposedAttributes = list(node.inputs.value) + list(node.outputs.value)
        edges = [(edge.src.fullName, edge.dst.fullName) for edge in node.graph.edges.values()
                 if edge.src in exposedAttributes or edge.dst in exposedAttributes]
        for _, dstName in edges:
            node.graph.removeEdge(node.graph.attribute(dstName))
        return edges

    @staticmethod
    def _graphAttribute(graph, fullName: str):
        """ Return the attribute of 'graph' named 'fullName', or None if it or its node does not exist. """
        if graph.node(fullName.split(".", 1)[0]) is None:
            return None
        return graph.attribute(fullName)

    @classmethod
    def _reconnectExposedAttributes(cls, node, edges: list):
        """
        Restore the edges whose attributes exist in the new scene.
        The other ones are kept in memory (they are not saved with the project) and restored when a scene exposing
        their attributes is set again, e.g. when the scene change is undone.
        """
        graph = node.graph
        if graph is None:
            return
        pendingEdges = []
        for srcName, dstName in edges + getattr(node, "_pendingSceneEdges", []):
            if (srcName, dstName) in pendingEdges:
                continue
            # Forget the edges whose other node has been removed
            if any(graph.node(name.split(".", 1)[0]) is None for name in (srcName, dstName)):
                continue
            srcAttr = cls._graphAttribute(graph, srcName)
            dstAttr = cls._graphAttribute(graph, dstName)
            if srcAttr is None or dstAttr is None:
                pendingEdges.append((srcName, dstName))
                continue
            # Do not replace a connection made since the edge was removed
            if dstAttr.isLink:
                continue
            try:
                graph.addEdge(srcAttr, dstAttr)
            except InvalidEdgeError:
                logger.warning(f"Cannot reconnect '{srcName}' to '{dstName}' with the new scene.")
        node._pendingSceneEdges = pendingEdges

    @staticmethod
    def _sceneInputValues(node) -> dict:
        """
        Return the values set on the exposed inputs, per scene: {scenePath: {attributeName: value}}.
        They are kept in memory (not saved with the project) to be restored when a scene is exposed again,
        e.g. when a scene change is undone, or when attributes hidden by useOnlyGraphIONodes are shown again.
        """
        if not hasattr(node, "_sceneInputValuesMemory"):
            node._sceneInputValuesMemory = {}
        return node._sceneInputValuesMemory

    def _rememberInputValues(self, node):
        """ Remember the values of the exposed inputs for the scene they come from. """
        if not node.exposedScene.value:
            return
        values = self._sceneInputValues(node).setdefault(node.exposedScene.value, {})
        values.update({attr.name: attr.value for attr in node.inputs.value if not attr.isLink})

    def _restoreInputValues(self, node):
        """ Restore the values remembered for the exposed scene on the inputs that are exposed and not linked. """
        for name, value in self._sceneInputValues(node).get(node.scene.value, {}).items():
            attr = node.inputs.value.get(name)
            if attr is not None and not attr.isLink:
                attr.value = value

    def onSceneChanged(self, node):
        self._updateExposedAttributes(node)

    def onUseOnlyGraphIONodesChanged(self, node):
        self._updateExposedAttributes(node)

    def _updateExposedAttributes(self, node):
        """
        Expose the attributes of the scene again, keeping the edges of the attributes that still exist
        and the values set on the inputs of this scene.
        """
        self._rememberInputValues(node)
        edges = self._disconnectExposedAttributes(node)
        self._clearAnySet(node.inputs)
        self._clearAnySet(node.outputs)
        self._exposeSceneAttributes(node)
        self._reconnectExposedAttributes(node, edges)
        self._restoreInputValues(node)
        node.exposedScene.value = node.scene.value

    def _exposeSceneAttributes(self, node):
        """ Expose the attributes of the input and output nodes of the scene in the node's inputs and outputs. """
        if not node.scene.value:
            return

        try:
            graph = loadGraph(node.scene.value)
        except Exception:
            logger.exception(f"The scene '{node.scene.value}' is not readable by Meshroom")
            return

        for inputNode in graph.findInputNodes():

            if node.useOnlyGraphIONodes.value and inputNode.nodeType != 'GraphInput':
                continue

            # Linked inputs are computed in the scene and cannot be overridden
            attributes = flattenAttributes(inputNode.getAttributes(), lambda attr: not attr.isInput or attr.isLink)
            self._exposeAttributes(node.inputs, attributes)

        # Only GraphOutput nodes are exposed: the output nodes are removed from the scene computed by meshroom_batch
        # (without -o), and their attributes are export settings rather than results
        for outputNode in graph.nodesOfType('GraphOutput'):
            self._exposeAttributes(node.outputs, flattenAttributes(outputNode.getAttributes()))
