"""
Execution contexts of the subgraphs: where the live nodes of a subgraph run ("python": the current
interpreter; plugins register the contexts of other software, see registerContext).

A context is opened once for a whole subgraph execution (all its iterations and nested subgraphs) and
closed at the end, so that a chain of live nodes costs no more than running their scripts one after the
other in the same interpreter. A context class registered under a name tells:

- whether it can run in the current interpreter (`isAvailable`): e.g. the context of a software needs its
  Python module, available in its interpreter or in its session;
- `interpreter()`: the command of an interpreter in which it is available, to run the subgraph in a
  separate process when it is not available here;
- `executables`: names of interpreters giving this context (a task node whose `pythonExecutable` contains one
  of them needs it);
- `open()` / `close()`: what to do before the first node and after the last one (e.g. load a file when the
  subgraph is not run from an open session, then quit). When the subgraph is run from the software itself
  (its Python shell), the context uses the running session and closes nothing.
"""
import importlib
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
    # Names of the interpreters giving this context (in the `pythonExecutable` of a task node needing it)
    executables = ()

    def __init__(self, ownsSession: bool = False):
        self.session = None
        # Whether the session is used only by the subgraph (a task of Meshroom or of a farm), so that close()
        # can clean it; False when the subgraph is run from a script or the shell of the software
        self.ownsSession = ownsSession
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

    def beginStep(self, iteration: int, frame: Optional[int]):
        """ Called before each run of the subgraph in a loop (e.g. to set the current frame of the software). """
        pass


class PythonContext(LiveContext):
    """ The current Python interpreter: nothing to open. """
    pass


def importable(moduleName: str) -> bool:
    """ Whether a module can be imported (e.g. the Python module of a software, for LiveContext.isAvailable). """
    try:
        importlib.import_module(moduleName)
        return True
    except ImportError:
        return False


_CONTEXTS: Dict[str, Type[LiveContext]] = {}
# Choices of the "context" parameter of the SubGraph node, completed as contexts are registered (by plugins)
CONTEXT_CHOICES: List[str] = ["auto"]


def registerContext(name: str, contextClass: Type[LiveContext]):
    """
    Register a context class under a name (replacing a previous one). A plugin registers the contexts of its
    software when its modules are imported (e.g. at the top of the module of its nodes).
    """
    contextClass.name = name
    _CONTEXTS[name] = contextClass
    if name not in CONTEXT_CHOICES:
        CONTEXT_CHOICES.append(name)


def contextClass(name: str) -> Type[LiveContext]:
    """ The context class registered under a name; raises KeyError with the known names otherwise. """
    if name not in _CONTEXTS:
        raise KeyError(f"Unknown subgraph context '{name}' (known: {', '.join(sorted(_CONTEXTS))}).")
    return _CONTEXTS[name]


def contextNames() -> List[str]:
    return sorted(_CONTEXTS)


def contextClasses() -> List[Type[LiveContext]]:
    """ The registered context classes, by name. """
    return [_CONTEXTS[name] for name in sorted(_CONTEXTS)]


def createContext(name: Optional[str], ownsSession: bool = False) -> LiveContext:
    """ A new (not opened) context of that name ("python" when empty), see LiveContext.ownsSession. """
    return contextClass(name or "python")(ownsSession)


registerContext("python", PythonContext)
