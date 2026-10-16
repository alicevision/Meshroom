"""Helpers of the Houdini live nodes (meshroom/nodes/houdini): parameters, ROP outputs."""
import ast
import os

from meshroom.core import desc

# Output file parameters of the usual ROPs, in the order they are looked for
OUTPUT_PARMS = ("vm_picture", "picture", "sopoutput", "lopoutput", "copoutput", "filename", "file", "outputimage")


def sceneInput():
    return desc.LiveValue(
        name="scene",
        label="Scene",
        description="Connect the previous Houdini node here to run after it.",
    )


def sceneOutput():
    return desc.LiveValue(
        name="sceneOut",
        label="Scene",
        description="The path of the current scene, to connect to the next Houdini node.",
    )


def samePath(a: str, b: str) -> bool:
    return bool(a) and bool(b) and os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def parseValue(text: str):
    """ A Python literal (number, tuple, list, quoted string...) or the text itself. """
    text = text.strip()
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def parseParmLines(text: str):
    """
    The parameter assignments written one per line: "path/parm = value" (a literal or a text) or
    "path/parm := expression" (an HScript expression). Empty lines and lines starting with # are skipped.
    Returns [(parm path, value, isExpression)].
    """
    assignments = []
    for number, line in enumerate((text or "").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":=" in line:
            path, _, value = line.partition(":=")
            assignments.append((path.strip(), value.strip(), True))
        elif "=" in line:
            path, _, value = line.partition("=")
            assignments.append((path.strip(), parseValue(value), False))
        else:
            raise ValueError(f"Line {number}: expected 'path/parm = value' or 'path/parm := expression'.")
    return assignments


def setParm(hou, path: str, value, isExpression: bool = False):
    """ Set a parameter (or a parameter tuple for a list / tuple value) from its full path. """
    if isExpression:
        parm = hou.parm(path)
        if parm is None:
            raise ValueError(f"No parameter '{path}'.")
        parm.setExpression(value, language=hou.exprLanguage.Hscript)
        return
    if isinstance(value, (list, tuple)):
        parmTuple = hou.parmTuple(path)
        if parmTuple is None:
            raise ValueError(f"No parameter tuple '{path}'.")
        parmTuple.set(value)
        return
    parm = hou.parm(path)
    if parm is None:
        raise ValueError(f"No parameter '{path}'.")
    if parm.isLocked():
        parm.lock(False)
    # A keyframed / expression parameter would ignore the value
    parm.deleteAllKeyframes()
    parm.set(value)


def ropOutputFile(rop, frame=None) -> str:
    """ The evaluated output file of a ROP (at a frame), empty if it has none of the usual parameters. """
    for name in OUTPUT_PARMS:
        parm = rop.parm(name)
        if parm is not None:
            return parm.evalAtFrame(frame) if frame is not None else parm.eval()
    return ""
