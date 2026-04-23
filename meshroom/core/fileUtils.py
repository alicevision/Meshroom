import os
import re

pattern = r"(?P<FILESTEM_PREFIX>.*?)(?P<FRAMEID_STR>[-._]\d+)?(?P<EXTENSION>\.\w{3,4})"
compiled_pattern = re.compile(pattern)
compiled_frameId = re.compile(r"(\D+)?(?P<FRAMEID>\d+$)")

def getFileElements(inputFilePath: str):

    filename = os.path.basename(inputFilePath)
    match = compiled_pattern.fullmatch(filename)
    frameId_str = None

    fileElements = {}
    if match:
        frameId_str = match.group("FRAMEID_STR")
        fileElements = {
            "<PATH>": inputFilePath,
            "<FILENAME>": filename,
            "<FILESTEM>": match.group("FILESTEM_PREFIX"),
            "<FILESTEM_PREFIX>": match.group("FILESTEM_PREFIX"),
            "<EXTENSION>": match.group("EXTENSION"),
        }

    if frameId_str is not None:
        fileElements["<FRAMEID_STR>"] = frameId_str
        fileElements["<FILESTEM>"] += frameId_str
        match_frameId = compiled_frameId.search(frameId_str)
        fileElements["<FRAMEID>"] = match_frameId.group("FRAMEID")

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
    return pattern.sub(replaceMatch, input)


compiled_element = re.compile(r"<\w*>")

def resolvePath(input, outputTemplate: str) -> str:

    if isinstance(input, str):
        replacements = getFileElements(input)
    else:
        replacements = getViewElements(input)

    resolved = replacePatterns(outputTemplate, compiled_element, replacements)

    return resolved
