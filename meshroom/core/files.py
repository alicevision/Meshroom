import json
from pathlib import Path
from typing import Dict, Tuple


MESHROOM_PROJECT_EXTENSION = ".mg"
MESHROOM_TEMPLATE_EXTENSION = ".mgt"
MESHROOM_LEGACY_TEMPLATE_EXTENSION = MESHROOM_PROJECT_EXTENSION


def extensionLower(filepath) -> str:
    return Path(filepath).suffix.lower()


def hasExtension(filepath, extensions: Tuple[str, ...]) -> bool:
    return extensionLower(filepath) in extensions


def withExtension(filepath, extension: str) -> str:
    """Return filepath with the requested extension if it has no matching suffix."""
    filepath = str(filepath)
    if extensionLower(filepath) != extension:
        filepath += extension
    return filepath


def isTemplateGraphData(graphData: Dict) -> bool:
    return bool(graphData.get("header", {}).get("template", False))


def isTemplateFile(filepath) -> bool:
    """Return whether filepath should be opened through the template flow."""
    path = Path(filepath)
    if extensionLower(path) == MESHROOM_TEMPLATE_EXTENSION:
        return True
    if extensionLower(path) != MESHROOM_LEGACY_TEMPLATE_EXTENSION:
        return False
    try:
        with open(path) as file:
            return isTemplateGraphData(json.load(file))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
