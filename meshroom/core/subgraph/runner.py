"""
Run a subgraph in the interpreter of its context when it is not available in the current one (e.g. from
the Meshroom user interface, run a Houdini subgraph in hython), exchanging JSON files:

    <interpreter> /path/to/runner.py request.json result.json

The request holds {"graph", "inputs", "context", "loop"}; the result {"outputs", "elapsed"} or
{"error", "nodeName"}. Values that cannot be written in JSON are returned as text.
"""
import json
import logging
import os
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Optional


def _storable(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def runRequest(requestPath: str, resultPath: str) -> int:
    """ Run the subgraph described in a request file and write the result file. Returns the exit code. """
    import meshroom.subgraph
    from meshroom.core.subgraph import Loop, SubGraphError, run

    with open(requestPath, "r", encoding="utf-8") as f:
        request = json.load(f)
    start = time.perf_counter()
    try:
        meshroom.subgraph.ensureNodes()
        outputs = run(request["graph"], request.get("inputs") or {}, context=request.get("context"),
                      loop=Loop.fromDict(request.get("loop")), ownsSession=True)
        result = {"outputs": {name: _storable(value) for name, value in outputs.items()},
                  "elapsed": time.perf_counter() - start}
        code = 0
    except SubGraphError as e:
        result = {"error": str(e), "nodeName": e.nodeName}
        code = 1
    with open(resultPath, "w", encoding="utf-8") as f:
        json.dump(result, f)
    return code


def runLive(graphData: dict, inputs: Optional[dict] = None, context: Optional[str] = None, loopData: Optional[dict] = None,
            logger: Optional[logging.Logger] = None) -> dict:
    """
    Run a subgraph here when its context is available, else in the interpreter of its context.
    Returns {"outputs", "elapsed", "interpreter"} or raises SubGraphError.
    """
    from .contexts import contextClass
    from .executor import Loop, SubGraphError, SubGraphPlan, environmentNode, resolveContextName, run

    plan = SubGraphPlan(graphData.get("graph", graphData))
    contextName = resolveContextName(plan, context)
    contextType = contextClass(contextName)
    if contextType.isAvailable():
        start = time.perf_counter()
        outputs = run(plan, inputs, context=contextName, loop=Loop.fromDict(loopData), logger=logger)
        return {"outputs": outputs, "elapsed": time.perf_counter() - start, "interpreter": ""}

    # The interpreter: the one set for the context (MESHROOM_HYTHON...), else the one of a task node of the
    # subgraph needing the context, in the process environment of its plugin (as the SubGraph task), else
    # the default one of the context
    environment = None if os.environ.get(contextType.interpreterVariable or "") else environmentNode(plan, contextName)
    interpreter = shlex.split(environment[0].pythonExecutable) if environment else contextType.interpreter()
    if not interpreter:
        raise SubGraphError(f"The '{contextName}' context is not available and has no interpreter.")
    with tempfile.TemporaryDirectory(prefix="meshroomSubGraph") as folder:
        requestPath, resultPath = os.path.join(folder, "request.json"), os.path.join(folder, "result.json")
        with open(requestPath, "w", encoding="utf-8") as f:
            json.dump({"graph": graphData, "inputs": inputs or {}, "context": contextName, "loop": loopData}, f,
                      default=str)
        arguments = [os.path.abspath(__file__), requestPath, resultPath]
        if environment:
            provider = environment[1]
            command = (provider.commandPrefix + " ".join(shlex.quote(arg) for arg in interpreter + arguments)
                       + provider.commandSuffix)
            env = provider.runtimeEnv if provider.processEnv else None
            (logger or logging).info(f"[SubGraph] {command}")
            process = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
        else:
            command = interpreter + arguments
            (logger or logging).info(f"[SubGraph] {' '.join(command)}")
            try:
                process = subprocess.run(command, capture_output=True, text=True)
            except FileNotFoundError:
                raise SubGraphError(
                    f"'{interpreter[0]}' not found: no node of the subgraph gives the environment of the '{contextName}' "
                    f"context; set {contextType.interpreterVariable} (e.g. \"rez env houdini -- hython\").")
        if not os.path.isfile(resultPath):
            raise SubGraphError(f"'{' '.join(interpreter)}' failed (exit code {process.returncode}):\n"
                                f"{(process.stderr or process.stdout)[-2000:]}")
        with open(resultPath, "r", encoding="utf-8") as f:
            result = json.load(f)
    if "error" in result:
        raise SubGraphError(result["error"])
    result["interpreter"] = " ".join(interpreter)
    return result


if __name__ == "__main__":
    # Run as a script by another interpreter (hython, mayapy, nuke -t): make Meshroom importable
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    sys.exit(runRequest(sys.argv[1], sys.argv[2]))
