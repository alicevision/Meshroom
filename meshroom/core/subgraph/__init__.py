"""
Subgraphs: chains of live nodes run in memory, in one context (Python, a software session...), as one
task. See executor.py for the execution, contexts.py for the contexts, ports.py for the ports, and
docs/subgraph.md.

From the Python shell of a software (e.g. Houdini), with Meshroom importable:

    import meshroom.subgraph
    outputs = meshroom.subgraph.run("/path/to/template.mgt", {"scene": "/path/shot.hip"})
"""
from .contexts import LiveContext, contextClass, contextNames, createContext, registerContext
from .executor import (Cancelled, Loop, RunContext, SubGraphError, SubGraphPlan, activeRunContext, contextOf, readGraphData,
                       resolveContextName, run, runGraph)

__all__ = [
    "Cancelled", "LiveContext", "Loop", "RunContext", "SubGraphError", "SubGraphPlan", "contextClass",
    "contextNames", "createContext", "readGraphData", "registerContext", "resolveContextName", "run", "runGraph",
    "activeRunContext", "contextOf",
]
