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


class SceneContext(LiveContext):
    """
    Base of the contexts of software working on a scene file (Houdini, Maya, Nuke).

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


class HoudiniContext(SceneContext):
    """
    Houdini: `ctx.context.session` is the hou module. Available in hython and in a Houdini session; from
    Meshroom or a farm, the subgraph runs in hython (the interpreter of the Houdini nodes of the subgraph,
    else MESHROOM_HYTHON). The current frame follows the frame loops. Scene: hou.hipFile.load / save are
    intercepted during a run (see SceneContext).
    """
    interpreterVariable = "MESHROOM_HYTHON"
    defaultInterpreter = "hython"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("hou")

    def open(self):
        import hou
        self.session = hou
        super().open()

    def currentScene(self) -> str:
        return self.session.hipFile.path()

    def _installGuard(self):
        context = self

        def loadWrapper(original):
            def load(file_name, *args, **kwargs):
                if context.skipLoad(file_name):
                    return None
                return original(file_name, *args, **kwargs)
            return load

        def saveWrapper(original):
            def save(file_name=None, *args, **kwargs):
                context.deferSave(file_name)
            return save

        self._patch(self.session.hipFile, "load", loadWrapper)
        self._patch(self.session.hipFile, "save", saveWrapper)

    def _load(self, path):
        # In a user session, Houdini asks whether to save the changes of the open scene
        load = self._original("load", self.session.hipFile.load)
        load(path, suppress_save_prompt=self.ownsSession, ignore_load_warnings=True)

    def _save(self, path):
        self._original("save", self.session.hipFile.save)(path)

    def _clear(self):
        self.session.hipFile.clear(suppress_save_prompt=True)

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.setFrame(frame)

    @staticmethod
    def preloadHostUsd():
        """
        In a Houdini process, import the USD Python modules (pxr) of Houdini before the node types are loaded,
        so that a plugin importing pxr gets the one of Houdini and not another USD found in PYTHONPATH (two USD
        libraries in one process make Houdini abort). Does nothing outside of Houdini or if pxr is imported.
        """
        import sys
        hfs = os.environ.get("HFS")
        if "hou" not in sys.modules or "pxr" in sys.modules or not hfs:
            return
        pythonLibs = os.path.join(hfs, "houdini", f"python{sys.version_info[0]}.{sys.version_info[1]}libs")
        if not os.path.isdir(os.path.join(pythonLibs, "pxr")):
            return
        if pythonLibs in sys.path:
            sys.path.remove(pythonLibs)
        sys.path.insert(0, pythonLibs)
        try:
            importlib.import_module("pxr.Tf")
        except ImportError as e:
            logging.warning(f"[SubGraph] Cannot preload the USD modules of Houdini: {e}")


def _samePath(a, b) -> bool:
    return bool(a) and bool(b) and os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


class MayaContext(SceneContext):
    """
    Maya: `ctx.context.session` is the maya.cmds module. Available in mayapy (initialized as standalone)
    and in a Maya session (the interpreter of the Maya nodes of the subgraph, else MESHROOM_MAYAPY).
    The current time follows the frame loops. Scene: cmds.file(open=...) / cmds.file(save=...) are
    intercepted during a run (see SceneContext).
    """
    interpreterVariable = "MESHROOM_MAYAPY"
    defaultInterpreter = "mayapy"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("maya.cmds")

    def open(self):
        import maya.cmds as cmds
        self._initialized = False
        if not hasattr(cmds, "about"):
            # mayapy: initialize Maya
            import maya.standalone
            maya.standalone.initialize(name="python")
            self._initialized = True
        self.session = cmds
        super().open()

    def currentScene(self) -> str:
        return self._original("file", self.session.file)(query=True, sceneName=True) or ""

    def _installGuard(self):
        context = self

        def fileWrapper(original):
            def file(*args, **kwargs):
                query = kwargs.get("query") or kwargs.get("q")
                if not query and (kwargs.get("open") or kwargs.get("o")) and args:
                    if context.skipLoad(args[0]):
                        return args[0]
                elif not query and (kwargs.get("save") or kwargs.get("s")):
                    context.deferSave()
                    return context.currentScene()
                return original(*args, **kwargs)
            return file

        self._patch(self.session, "file", fileWrapper)

        # Maya is initialized (a Maya session, or mayapy initialized by `open`): the nodes written for mayapy
        # initialize / uninitialize it themselves, which fails in a Maya session ("can not be called inside
        # of Maya") or would end the session for the next nodes
        try:
            import maya.standalone as standalone
        except ImportError:
            return

        def initializeWrapper(original):
            def initialize(*args, **kwargs):
                logging.info("[SubGraph] maya.standalone.initialize: Maya is already initialized.")
            return initialize

        def uninitializeWrapper(original):
            def uninitialize(*args, **kwargs):
                logging.info("[SubGraph] maya.standalone.uninitialize: done at the end of the subgraph.")
            return uninitialize

        self._patch(standalone, "initialize", initializeWrapper)
        self._patch(standalone, "uninitialize", uninitializeWrapper)

    def _load(self, path):
        self._original("file", self.session.file)(path, open=True, force=True)

    def _save(self, path):
        file = self._original("file", self.session.file)
        if not _samePath(self.currentScene(), path):
            file(rename=path)
        file(save=True, force=True, type="mayaAscii" if str(path).lower().endswith(".ma") else "mayaBinary")

    def _clear(self):
        self._original("file", self.session.file)(new=True, force=True)

    def close(self):
        super().close()
        if self.ownsSession and self._initialized:
            import maya.standalone
            maya.standalone.uninitialize()

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.currentTime(frame, edit=True)


class NukeContext(SceneContext):
    """
    Nuke: `ctx.context.session` is the nuke module. Available in a Nuke session and with "nuke -t" (the
    interpreter of the Nuke nodes of the subgraph, else MESHROOM_NUKE). The current frame follows the
    frame loops. Script: nuke.scriptOpen / scriptSave / scriptSaveAs are intercepted during a run (see
    SceneContext).
    """
    interpreterVariable = "MESHROOM_NUKE"
    defaultInterpreter = "nuke -t"

    @classmethod
    def isAvailable(cls) -> bool:
        return _importable("nuke")

    def open(self):
        import nuke
        self.session = nuke
        super().open()

    def currentScene(self) -> str:
        try:
            return self.session.scriptName()
        except RuntimeError:
            # Untitled script
            return ""

    def _installGuard(self):
        context = self

        def openWrapper(original):
            def scriptOpen(filename, *args, **kwargs):
                if context.skipLoad(filename):
                    return None
                return original(filename, *args, **kwargs)
            return scriptOpen

        def saveWrapper(original):
            def scriptSave(filename=None, *args, **kwargs):
                context.deferSave(filename or None)
                return True
            return scriptSave

        def saveAsWrapper(original):
            def scriptSaveAs(filename=None, *args, **kwargs):
                context.deferSave(filename or None)
            return scriptSaveAs

        self._patch(self.session, "scriptOpen", openWrapper)
        self._patch(self.session, "scriptSave", saveWrapper)
        self._patch(self.session, "scriptSaveAs", saveAsWrapper)

    def _load(self, path):
        if self.ownsSession:
            self.session.scriptClear()
        self._original("scriptOpen", self.session.scriptOpen)(path)

    def _save(self, path):
        self._original("scriptSaveAs", self.session.scriptSaveAs)(path, 1)

    def _clear(self):
        self.session.scriptClear()

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
