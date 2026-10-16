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


def _importable(moduleName: str) -> bool:
    try:
        importlib.import_module(moduleName)
        return True
    except ImportError:
        return False


class HoudiniContext(LiveContext):
    """
    Houdini: `ctx.context.session` is the hou module. Available in hython and in a Houdini session; from
    Meshroom or a farm, the subgraph runs in hython (MESHROOM_HYTHON to change the command). The current
    frame of Houdini follows the frame loops.

    During a run, the task nodes written to open and save the scene themselves (hou.hipFile.load / save in
    each node) share the session: loading the scene already open does nothing, and the saves are grouped
    in one save at the end of a Meshroom task (none from a Houdini session, unless a HoudiniSave node asks
    for it). The scene is saved before another scene is loaded in a Meshroom task.
    """
    interpreterVariable = "MESHROOM_HYTHON"
    defaultInterpreter = "hython"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("hou")

    def open(self):
        import hou
        super().open()
        self.session = hou
        # Scene requested by the saves of the nodes, saved at the end (or before loading another scene)
        self.pendingSave = None
        self._realLoad = self._realSave = None
        self._installSceneGuard()

    def _installSceneGuard(self):
        """ Replace hou.hipFile.load / save during the run (see the class documentation). """
        hipFile = self.session.hipFile
        realLoad, realSave = hipFile.load, hipFile.save

        def load(file_name, *args, **kwargs):
            if _samePath(hipFile.path(), file_name):
                logging.info(f"[SubGraph] {file_name} is the open scene: not loaded again.")
                return None
            self._flushPendingSave()
            return realLoad(file_name, *args, **kwargs)

        def save(file_name=None, *args, **kwargs):
            self.pendingSave = file_name or hipFile.path()
            logging.info(f"[SubGraph] Save of {self.pendingSave} grouped at the end of the subgraph.")

        try:
            hipFile.load, hipFile.save = load, save
        except (AttributeError, TypeError) as e:
            logging.warning(f"[SubGraph] Cannot intercept hou.hipFile.load / save ({e}): each node loads and saves the scene.")
            return
        self._realLoad, self._realSave = realLoad, realSave

    def _removeSceneGuard(self):
        if self._realLoad is not None:
            hipFile = self.session.hipFile
            hipFile.load, hipFile.save = self._realLoad, self._realSave

    def loadScene(self, path: str):
        """ Load a scene, unless it is the open one (the pending save is done first in a Meshroom task). """
        if _samePath(self.session.hipFile.path(), path):
            return
        self._flushPendingSave()
        (self._realLoad or self.session.hipFile.load)(path, suppress_save_prompt=True, ignore_load_warnings=True)

    def saveScene(self, path: Optional[str] = None):
        """ Save the scene now (to `path`, else to the pending save path, else to its current file). """
        path = path or self.pendingSave or self.session.hipFile.path()
        (self._realSave or self.session.hipFile.save)(path)
        self.pendingSave = None

    def discardPendingSave(self):
        self.pendingSave = None

    def _flushPendingSave(self):
        if self.pendingSave and self.ownsSession:
            self.saveScene(self.pendingSave)
        elif self.pendingSave:
            logging.warning(f"[SubGraph] The changes of {self.pendingSave} are not saved (Houdini session).")
            self.pendingSave = None

    def close(self):
        try:
            if self.isOpen and self.session is not None:
                self._flushPendingSave()
        finally:
            self._removeSceneGuard()
            if self.ownsSession and self.session is not None:
                # Leave the hython session empty
                self.session.hipFile.clear(suppress_save_prompt=True)
            super().close()

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.setFrame(frame)


def _samePath(a, b) -> bool:
    return bool(a) and bool(b) and os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


class MayaContext(LiveContext):
    """
    Maya: `ctx.context.session` is the maya.cmds module. Available in mayapy (initialized as standalone)
    and in a Maya session (MESHROOM_MAYAPY to change the command).
    """
    interpreterVariable = "MESHROOM_MAYAPY"
    defaultInterpreter = "mayapy"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("maya.cmds")

    def open(self):
        import maya.cmds as cmds
        super().open()
        self._initialized = False
        if not hasattr(cmds, "about"):
            # mayapy: initialize Maya
            import maya.standalone
            maya.standalone.initialize(name="python")
            self._initialized = True
        self.session = cmds

    def close(self):
        if self.ownsSession and self._initialized:
            import maya.standalone
            maya.standalone.uninitialize()
        super().close()

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.currentTime(frame, edit=True)


class NukeContext(LiveContext):
    """
    Nuke: `ctx.context.session` is the nuke module. Available in a Nuke session and with "nuke -t"
    (MESHROOM_NUKE to change the command).
    """
    interpreterVariable = "MESHROOM_NUKE"
    defaultInterpreter = "nuke -t"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("nuke")

    def open(self):
        import nuke
        super().open()
        self.session = nuke

    def close(self):
        if self.ownsSession and self.session is not None:
            self.session.scriptClear()
        super().close()

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.frame(frame)


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


def createContext(name: Optional[str], ownsSession: bool = False) -> LiveContext:
    """ A new (not opened) context of that name ("python" when empty), see LiveContext.ownsSession. """
    return contextClass(name or "python")(ownsSession)


registerContext("python", PythonContext)
registerContext("houdini", HoudiniContext)
registerContext("maya", MayaContext)
registerContext("nuke", NukeContext)
