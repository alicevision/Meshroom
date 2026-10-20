"""
Subgraphs: chains of live nodes run in memory, in one context (Python, a software session...), as one
task. See executor.py for the execution, contexts.py for the contexts, ports.py for the ports, and
docs/subgraph.md.

From a Python script or the Python shell of a software, with Meshroom importable:

    import meshroom.subgraph
    outputs = meshroom.subgraph.run("/path/to/template.mgt", {"scene": "/path/shot.hip"})
"""
from .contexts import LiveContext, PythonContext, contextClass, contextNames, createContext, importable, registerContext
from .executor import (Cancelled, Loop, RunContext, SubGraphError, SubGraphPlan, activeRunContext, contextOf, readGraphData,
                       resolveContextName, run, runGraph)

__all__ = [
    "Cancelled", "LiveContext", "PythonContext", "Loop", "RunContext", "SubGraphError", "SubGraphPlan", "contextClass",
    "contextNames", "createContext", "importable", "readGraphData", "registerContext", "resolveContextName", "run", "runGraph",
    "activeRunContext", "contextOf",
]
