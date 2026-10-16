"""
Shared parts of the subgraph node descriptors (meshroom/nodes/subgraph): the attributes of the nodes
running a subgraph (SubGraph, LiveSubGraph) and the synchronization of their ports.
"""
import json
import logging
import os
from typing import List, Optional, Tuple

from meshroom.core import desc

from .executor import Loop, SubGraphError, SubGraphPlan, readGraphData
from .ports import PORT_TYPES, parsePortSpec, syncAnySet


def portSpecParam(name: str = "portSpec", label: str = "Ports", value: str = "") -> desc.StringParam:
    """ A port spec attribute (see ports.py). """
    return desc.StringParam(
        name=name,
        label=label,
        description="Ports, separated by commas, each optionally followed by a type: 'image, count:IntParam'.\n"
                    f"Types: {', '.join(PORT_TYPES)} (LiveValue by default: any value).",
        value=value,
        invalidate=False,
    )


def subGraphSourceParams() -> list:
    """ Where a subgraph is read from: embedded in the node and/or a template file. """
    return [
        desc.File(
            name="template",
            label="Template",
            description="Template (.mgt / .mg) of the subgraph, used when the subgraph is not embedded.",
            value="",
        ),
        desc.StringParam(
            name="subGraph",
            label="Embedded Subgraph",
            description="The subgraph saved in the node (its nodes in JSON), edited by entering the node.\n"
                        "When it is set, the template is not used.",
            value="",
            advanced=True,
        ),
        desc.PushButtonParam(
            name="makeLocal",
            label="Make Local",
            description="Copy the template in the node, to edit it without changing the template file.",
            enabled=lambda node: bool(node.template.value) and not node.subGraph.value,
        ),
    ]


def contextParam() -> desc.ChoiceParam:
    from .contexts import contextNames
    return desc.ChoiceParam(
        name="context",
        label="Context",
        description="Software in which the live nodes run, opened once for the whole subgraph.\n"
                    " - auto: the one needed by the nodes (Python if none).",
        value="auto",
        values=["auto"] + contextNames(),
    )


def loopParams(withFarmSplit: bool = False) -> list:
    """ The loop attributes (see executor.Loop); `withFarmSplit` adds the frames per task of the farm. """
    params = [
        desc.ChoiceParam(
            name="loopMode",
            label="Loop",
            description="How the subgraph is repeated:\n"
                        " - none: once.\n"
                        " - count: a number of iterations, the outputs feeding the inputs of the same name.\n"
                        " - frames: once per frame of a frame range.",
            value="none",
            values=list(Loop.MODES),
        ),
        desc.IntParam(
            name="iterations",
            label="Iterations",
            description="Number of iterations (count loop).",
            value=1,
            range=(0, 100, 1),
            enabled=lambda node: node.loopMode.value == "count",
        ),
        desc.IntParam(
            name="frameFirst",
            label="First Frame",
            description="First frame of the frame loop.",
            value=1001,
            range=None,
            enabled=lambda node: node.loopMode.value == "frames",
        ),
        desc.IntParam(
            name="frameLast",
            label="Last Frame",
            description="Last frame of the frame loop (included).",
            value=1001,
            range=None,
            enabled=lambda node: node.loopMode.value == "frames",
        ),
        desc.IntParam(
            name="frameStep",
            label="Frame Step",
            description="Step between the frames of the frame loop.",
            value=1,
            range=(1, 10, 1),
            enabled=lambda node: node.loopMode.value == "frames",
        ),
    ]
    if withFarmSplit:
        params.append(desc.IntParam(
            name="framesPerTask",
            label="Frames Per Task",
            description="Frames run by each task (on several machines of a farm); 0: all the frames in one task.",
            value=0,
            range=(0, 100, 1),
            enabled=lambda node: node.loopMode.value == "frames",
        ))
    return params


def loopFromValues(values: dict) -> Loop:
    """ The Loop described by the loop attributes values {name: value}. """
    return Loop(values.get("loopMode") or "none", values.get("iterations", 1), values.get("frameFirst", 1),
                values.get("frameLast", 1), values.get("frameStep", 1))


def loopFromNode(node) -> Loop:
    return loopFromValues({name: node.attribute(name).value for name in
                           ("loopMode", "iterations", "frameFirst", "frameLast", "frameStep")})


def graphSource(subGraph: str, template: str):
    """ The source of a subgraph (see executor.readGraphData): the embedded one, else the template. """
    if subGraph and subGraph.strip():
        return subGraph
    if template:
        return template
    return None


def nodeGraphSource(node):
    return graphSource(node.subGraph.value, node.template.value)


def nodePlan(node) -> Optional[SubGraphPlan]:
    """ The plan of the subgraph of a node, None if it has none. """
    source = nodeGraphSource(node)
    return SubGraphPlan.cached(source) if source is not None else None


def subGraphPorts(source) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """ The input and output (name, type) ports of a subgraph; empty when it cannot be read (logged). """
    if source is None:
        return [], []
    try:
        plan = SubGraphPlan.cached(source)
    except (SubGraphError, ValueError, OSError) as e:
        logging.warning(f"[SubGraph] Cannot read the subgraph: {e}")
        return [], []
    return plan.inputPortTypes, plan.outputPortTypes


def syncSubGraphPorts(node):
    """ Make the `ins` / `outs` attributes of a node running a subgraph match the ports of the subgraph. """
    if node.subGraph.isLink or node.template.isLink:
        return
    inputs, outputs = subGraphPorts(nodeGraphSource(node))
    syncAnySet(node.attribute("ins"), inputs)
    syncAnySet(node.attribute("outs"), outputs)


def syncSpecPorts(node, specName: str, anySetName: str):
    """ Make the children of an AnySet attribute match a port spec attribute. """
    spec = node.attribute(specName)
    if spec.isLink:
        return
    syncAnySet(node.attribute(anySetName), parsePortSpec(spec.value))


def makeLocal(node):
    """ Copy the template of a node in its embedded subgraph (JSON of the nodes). """
    template = node.template.value
    if not template or not os.path.isfile(template):
        raise SubGraphError(f"Template not found: {template}", node.name)
    node.subGraph.value = json.dumps(readGraphData(template), indent=1)
    node.template.value = ""
