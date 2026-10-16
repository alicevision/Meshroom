"""
Execution contexts of the subgraphs: the software in which the live nodes of a subgraph run.

A context is opened once for a whole subgraph execution (all its iterations and nested subgraphs) and
closed at the end, so that a chain of live nodes costs no more than running their scripts one after the
other in the same interpreter. A context class registered under a name (e.g. "python", "houdini") tells:

- whether it can run in the current interpreter (`isAvailable`): e.g. the Houdini context needs the `hou`
  module, available in hython or in a Houdini session;
- `interpreter()`: the command of an interpreter in which it is available (e.g. "hython"), used to run
  the subgraph in a separate process when it is not available here (meshroom_compute on the farm);
- `open()` / `close()`: what to do before the first node and after the last one (e.g. load a scene file
  when the subgraph is not run from an open session, then quit). When the subgraph is run from the
  software itself (its Python shell), the context uses the running session and closes nothing.
"""
import os
import shlex
from typing import Dict, List, Optional, Type


class LiveContext:
    """
    Base of the contexts. The live nodes reach it with `ctx.context` (e.g. `ctx.context.session` for a
    software module, `ctx.context.ownsSession` to know whether the session was opened for the subgraph).
    """

    # Name of the context, set by registerContext
    name = ""
    # Environment variable overriding the interpreter command
    interpreterVariable = ""
    # Default interpreter command (empty: the current Python)
    defaultInterpreter = ""

    def __init__(self):
        self.session = None
        # Whether open() started a session that close() ends (False when run from the software itself)
        self.ownsSession = False
        self.isOpen = False

    @classmethod
    def isAvailable(cls) -> bool:
        """ Whether the context can run in the current interpreter. """
        return True

    @classmethod
    def interpreter(cls) -> List[str]:
        """ The command of an interpreter where the context is available (environment variable first). """
        command = os.environ.get(cls.interpreterVariable, "") if cls.interpreterVariable else ""
        command = command or cls.defaultInterpreter
        return shlex.split(command) if command else []

    def open(self):
        self.isOpen = True

    def close(self):
        self.isOpen = False


class PythonContext(LiveContext):
    """ The current Python interpreter: nothing to open. """
    pass


_CONTEXTS: Dict[str, Type[LiveContext]] = {}


def registerContext(name: str, contextClass: Type[LiveContext]):
    """ Register a context class under a name (replacing a previous one). """
    contextClass.name = name
    _CONTEXTS[name] = contextClass


def contextClass(name: str) -> Type[LiveContext]:
    """ The context class registered under a name; raises KeyError with the known names otherwise. """
    if name not in _CONTEXTS:
        raise KeyError(f"Unknown subgraph context '{name}' (known: {', '.join(sorted(_CONTEXTS))}).")
    return _CONTEXTS[name]


def contextNames() -> List[str]:
    return sorted(_CONTEXTS)


def createContext(name: Optional[str]) -> LiveContext:
    """ A new (not opened) context of that name ("python" when empty). """
    return contextClass(name or "python")()


registerContext("python", PythonContext)
