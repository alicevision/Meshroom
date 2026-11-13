#!/usr/bin/env python
# coding:utf-8

import os
import subprocess
import sys

_MESHROOM_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_failedCommandExitCode(tmp_path):
    """ meshroom_plugins exits with an error code when a command fails. """
    # An existing, empty local plugins folder: no registry is loaded, nothing is downloaded.
    env = {**os.environ, "MESHROOM_LOCAL_PLUGINS_PATH": str(tmp_path),
           "PYTHONPATH": os.pathsep.join([_MESHROOM_ROOT, os.environ.get("PYTHONPATH", "")])}
    command = [sys.executable, os.path.join(_MESHROOM_ROOT, "bin", "meshroom_plugins"), "info", "noSuchPlugin"]
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert "No plugin found for: noSuchPlugin." in result.stdout
