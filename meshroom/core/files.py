from __future__ import annotations

import json
import os
import shutil
import tempfile

from pathlib import Path
from typing import Dict, Tuple
from contextlib import contextmanager

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


def isSafeFolderName(name) -> bool:
    """ Return whether "name" is safe to use as a single folder name. """
    return isinstance(name, str) and name not in ("", "..") and Path(name).name == name


def atomicWriteFile(path: Path, data: str | bytes, mode: str = "w",
                    prefix: str = tempfile.gettempprefix()) -> None:
    """
    Write "data" to "path" atomically: written to a temporary file in the same folder first, then
    moved into place with os.replace(), so a reader never observes a partial file.

    Args:
        path: the file to write.
        data: the content to write ("str" for a text mode, "bytes" for a binary mode).
        mode: the open mode, "w" (text) or "wb" (binary).
        prefix: the prefix of the temporary file's random name, created directly under "path"'s folder.
    """
    path = Path(path)
    fd, tmpPath = tempfile.mkstemp(dir=path.parent, prefix=prefix)
    try:
        with os.fdopen(fd, mode) as f:
            f.write(data)
        os.replace(tmpPath, path)
    except BaseException:
        os.remove(tmpPath)
        raise


@contextmanager
def scratchFolder(parentPath: Path, prefix: str = tempfile.gettempprefix()):
    """
    Context manager yielding a scratch folder created inside "parentPath".
    Removed automatically once the "with" block exits, whether or not something was moved out of it.

    Args:
        parentPath: the folder the scratch folder is created into, and whatever is produced should be
                    moved into.
        prefix: the prefix of the scratch folder's random name.

    Yields:
        Path: the scratch folder.
    """
    parentPath = Path(parentPath)
    parentPath.mkdir(parents=True, exist_ok=True)
    tmpFolder = Path(tempfile.mkdtemp(dir=parentPath, prefix=prefix))
    try:
        yield tmpFolder
    finally:
        shutil.rmtree(tmpFolder, ignore_errors=True)
