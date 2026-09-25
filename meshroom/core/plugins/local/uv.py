from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys

from typing import Callable, Optional

import meshroom
from meshroom.env import EnvVar


# Markers in "uv sync" / "uv pip install" output, with the install progress (0 to 1).
_UV_PROGRESS_MARKERS = (
    (re.compile(r"Resolved\s+\d+\s+package"), 0.4),
    (re.compile(r"Prepared\s+\d+\s+package"), 0.8),
    (re.compile(r"Installed\s+\d+\s+package"), 0.9),
)


def findUv() -> Optional[str]:
    """
    Locate the "uv" executable Meshroom should use to install plugin dependencies.

    Resolution order:
        1. The "MESHROOM_UV_PATH" environment variable, if it points to an existing file.
        2. An "uv" executable found on PATH.
        3. An "uv" executable sitting next to the current interpreter/executable
           (covers frozen builds shipping their own copy).

    Returns:
        str | None: the absolute path to the "uv" executable, or None if none was found.
    """
    fromEnv = EnvVar.get(EnvVar.MESHROOM_UV_PATH)
    if fromEnv and os.path.isfile(fromEnv):
        return fromEnv

    fromPath = shutil.which("uv")
    if fromPath:
        return fromPath

    exeName = "uv.exe" if sys.platform == "win32" else "uv"
    bundled = os.path.join(os.path.dirname(sys.executable), exeName)
    if os.path.isfile(bundled):
        return bundled

    return None


def pythonForUv() -> str:
    """
    Return the value to pass to uv's "--python" option ("uv venv" / "uv sync") so a plugin's
    virtual environment is built with the same Python as the one running Meshroom.

    - Running from sources: "sys.executable" is the running interpreter, so use it directly.
    - Frozen build (cx_Freeze): "sys.executable" is the application binary, not a usable
      interpreter, so fall back to the embedded "<major>.<minor>" version string.
      The exact minor version is required: the plugin's node processes run with this venv's
      "python" and get Meshroom's "lib/" folder on their PYTHONPATH, which only contains
      version-specific content (".pyc" bytecode of Meshroom), so another interpreter version
      cannot import it.
    """
    if meshroom.isFrozen:
        return f"{sys.version_info.major}.{sys.version_info.minor}"
    return sys.executable


def parseUvProgress(line: str, progress: float) -> float:
    """
    Return the install progress (0 to 1) after the "uv" output "line", given the current "progress".
    The progress only moves forward: an install-phase marker jumps to its value, any other line
    creeps toward (without reaching) the next marker so the progress does not look stuck.

    Args:
        line: a line of the "uv" output.
        progress: the current progress, from 0 to 1.

    Returns:
        float: the new progress, from 0 to 1.
    """
    for marker, value in _UV_PROGRESS_MARKERS:
        if marker.search(line):
            return max(progress, value)
    nextValue = next((value for _, value in _UV_PROGRESS_MARKERS if value > progress), 1.0)
    return progress + (nextValue - progress) * 0.05  # Fraction of the way to the next marker.


def runUv(cmd: list[str], env: Optional[dict] = None) -> int:
    """
    Run the "uv" command "cmd".

    Args:
        cmd: the command (the "uv" executable + arguments) to run.
        env: environment variables to set on top of the current environment, if any.

    Returns:
        int: the exit code of the command.
    """
    logging.info(f"Running: {' '.join(cmd)}")

    process = subprocess.Popen(cmd, env={**os.environ, **env} if env else None)

    process.wait()
    return process.returncode


def runUvWithProgress(cmd: list[str], onLine: Callable[[str], None], env: Optional[dict] = None,
                      output: Optional[list[str]] = None) -> int:
    """
    Run the "uv" command "cmd", calling "onLine" with each line of its merged stdout/stderr as it streams.

    If "onLine" raises (e.g. to cancel), the command is terminated and the exception propagates.

    Args:
        cmd: the command (the "uv" executable + arguments) to run.
        onLine: called with each output line, without its trailing newline.
        env: environment variables to set on top of the current environment, if any.
        output: if set, each output line is appended to it.

    Returns:
        int: the exit code of the command.
    """
    logging.info(f"Running: {' '.join(cmd)}")

    # Merge stderr into stdout and read line-buffered, so output streams live.
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, env={**os.environ, **env} if env else None)
    with process:
        try:
            for line in process.stdout:
                line = line.rstrip("\n")
                if output is not None:
                    output.append(line)
                onLine(line)
        except BaseException:
            process.terminate()
            raise
    return process.returncode
