"""
Hidden edges of the graph editor (key H): an edge stays in the graph but is drawn as a stub on its two
pins. The names of the hidden inputs of a node, relative to it (e.g. "input", "inputs[2]"), are stored
comma-separated in its "hiddenInputs" internal attribute, so that they are saved with the graph.
"""
import re
from typing import List

HIDDEN_INPUTS = "hiddenInputs"


def relativeName(attribute) -> str:
    """ Name of an attribute within its node (e.g. "input", "inputs[0]", "group.value"). """
    return attribute.fullName.split(".", 1)[1]


def hiddenNames(node) -> List[str]:
    """ The names of the hidden inputs of a node ([] if it cannot hide edges). """
    if not node.hasInternalAttribute(HIDDEN_INPUTS):
        return []
    return [name for name in node.internalAttribute(HIDDEN_INPUTS).value.split(",") if name]


def isHidden(attribute) -> bool:
    """ Whether the edge going to the input `attribute` is hidden. """
    return relativeName(attribute) in hiddenNames(attribute.node)


def withNames(value: str, names, hide: bool) -> str:
    """ A "hiddenInputs" value with `names` added (hide) or removed. """
    current = [name for name in (value or "").split(",") if name]
    if hide:
        current += [name for name in names if name not in current]
    else:
        current = [name for name in current if name not in names]
    return ",".join(current)


def afterListRemoval(value: str, listName: str, index: int) -> str:
    """
    A "hiddenInputs" value once the element `index` of the list attribute `listName` is removed: its own
    hidden edge is forgotten and the hidden elements after it move down by one, like the elements themselves.
    """
    pattern = re.compile(r"^" + re.escape(listName) + r"\[(\d+)\](.*)$")
    names = []
    for name in (value or "").split(","):
        match = pattern.match(name)
        if match:
            position = int(match.group(1))
            if position == index:
                continue
            if position > index:
                name = f"{listName}[{position - 1}]{match.group(2)}"
        if name:
            names.append(name)
    return ",".join(names)
