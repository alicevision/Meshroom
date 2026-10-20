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
import logging
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


def _samePath(a, b) -> bool:
    return bool(a) and bool(b) and os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


class SceneContext(LiveContext):
    """
    Base of the contexts of software working on a scene file (e.g. a 3D or compositing software).

    During a run, the nodes written to load and save the scene themselves (each node of a pipeline plugin
    loads the scene, changes it, saves it) share the session: loading the scene already open does nothing,
    and their saves are grouped in one save, at the end of a Meshroom task or at a "Save" node (none in a
    session of the software, unless the Save node asks for it). The scene is saved before another scene is
    loaded in a Meshroom task. Subclasses replace the load / save functions of the software with `_patch`
    (in `_installGuard`) and give `currentScene`, `_load`, `_save`, `_clear`.
    """

    def open(self):
        super().open()
        # Scene requested by the saves of the nodes, saved at the end (or before loading another scene)
        self.pendingSave = None
        self._patches = []
        self._originals = {}
        self._installGuard()

    # To implement by the software contexts

    def currentScene(self) -> str:
        """ The path of the open scene ("" if it has none). """
        return ""

    def _installGuard(self):
        pass

    def _load(self, path: str):
        """ Load a scene (with the real function of the software). """
        raise NotImplementedError()

    def _save(self, path: str):
        """ Save the scene to a path (with the real function of the software). """
        raise NotImplementedError()

    def _clear(self):
        """ Leave the session empty (a session owned by the run, at its end). """
        pass

    # Common behaviour

    def _patch(self, owner, name: str, makeWrapper):
        """ Replace owner.name by makeWrapper(original) during the run (restored when the context closes). """
        original = getattr(owner, name)
        try:
            setattr(owner, name, makeWrapper(original))
        except (AttributeError, TypeError) as e:
            logging.warning(f"[SubGraph] Cannot intercept {name} ({e}): each node loads and saves the scene.")
            return
        self._originals[name] = original
        self._patches.append((owner, name, original))

    def _original(self, name: str, default=None):
        return self._originals.get(name, default)

    def isOpenScene(self, path) -> bool:
        return _samePath(self.currentScene(), path)

    def skipLoad(self, path) -> bool:
        """ For the load wrappers: whether loading `path` is skipped (open scene); else the pending save is done. """
        if self.isOpenScene(path):
            logging.info(f"[SubGraph] {path} is the open scene: not loaded again.")
            return True
        if not self.ownsSession and self.currentScene():
            # In the session of the software (its shell, a tool): the open scene prevails, it is never replaced
            # (unsaved changes would be lost), e.g. by a node loading the last version saved on disk
            logging.warning(f"[SubGraph] {path} not loaded: the open scene ({self.currentScene()}) is used.")
            return True
        self._flushPendingSave()
        return False

    def deferSave(self, path=None):
        """ For the save wrappers: remember the save, done once later. """
        self.pendingSave = path or self.currentScene()
        logging.info(f"[SubGraph] Save of {self.pendingSave} grouped at the end of the subgraph.")

    def loadScene(self, path: str):
        """ Load a scene, unless it is the open one (the pending save is done first in a Meshroom task). """
        if self.isOpenScene(path):
            return
        self._flushPendingSave()
        self._load(path)

    def saveScene(self, path: Optional[str] = None):
        """ Save the scene now (to `path`, else to the pending save path, else to its current file). """
        path = path or self.pendingSave or self.currentScene()
        self._save(path)
        self.pendingSave = None

    def discardPendingSave(self):
        self.pendingSave = None

    def _flushPendingSave(self):
        if self.pendingSave and self.ownsSession:
            self.saveScene(self.pendingSave)
        elif self.pendingSave:
            logging.warning(f"[SubGraph] The changes of {self.pendingSave} are not saved (session of the software).")
            self.pendingSave = None

    def close(self):
        try:
            if self.isOpen and self.session is not None:
                self._flushPendingSave()
        finally:
            for owner, name, original in reversed(self._patches):
                setattr(owner, name, original)
            self._patches = []
            if self.ownsSession and self.session is not None:
                self._clear()
            super().close()


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
