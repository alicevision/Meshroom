import os
import re

def getFileElements(inputFilePath: str):

    filename = os.path.basename(inputFilePath)
    pattern = r"(?P<FILESTEM>.*?)(?P<FRAME_ID>[-._]\d+)?(?P<EXTENSION>\.\w{3,4})"
    match = re.search(pattern, filename)
    frameId = match.group("FRAME_ID")
    
    fileElements = {}
    if match:
        fileElements = {
            "<PATH>": inputFilePath,
            "<FILENAME>": filename,
            "<FILESTEM>": match.group("FILESTEM"),
            "<FILESTEM_PREFIX>": match.group("FILESTEM"),
            "<EXTENSION>": match.group("EXTENSION"),
        }
    if frameId is not None:
        fileElements["<FRAMEID>"] = frameId
        fileElements["<FILESTEM>"] += frameId

    return fileElements


def getViewElements(vp):

    vpPath = vp.childAttribute("path").value

    viewElements = getFileElements(vpPath)

    viewElements["<VIEW_ID>"] = str(vp.childAttribute("viewId").value)
    viewElements["<INTRINSIC_ID>"] = str(vp.childAttribute("intrinsicId").value)
    viewElements["<POSE_ID>"] = str(vp.childAttribute("poseId").value)

    return viewElements


def replacePatterns(input, pattern, replacements):
    # Use all substrings of "input" matching the regex "pattern" as a key to substitute themselves by their value in the dictionary "replacements".
    # If "replacements" does not contain the key, the key is removed from "input" to build the resolved string.
    def replaceMatch(match):
        key = match.group()
        return replacements.get(key, "")
    return re.sub(pattern, replaceMatch, input)


def resolvePath(input, outputTemplate: str) -> str:

    if isinstance(input, str):
        replacements = getFileElements(input)
    else:
        replacements = getViewElements(input)

    resolved = replacePatterns(outputTemplate, r"<\w*>", replacements)

    return resolved

