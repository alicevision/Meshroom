# desc/node.py

import enum
from inspect import getfile, getattr_static
from pathlib import Path
import logging
import shlex
import shutil
import sys
import signal
import subprocess

import psutil

from meshroom import _MESHROOM_ROOT
from meshroom.core import cgroup
from meshroom.core.utils import VERBOSE_LEVEL

from .computation import Level, StaticNodeSize
from .attribute import Attribute, ChoiceParam, ColorParam, IntParam, StringParam

_MESHROOM_COMPUTE = (Path(_MESHROOM_ROOT) / "bin" / "meshroom_compute").as_posix()
_MESHROOM_COMPUTE_DEPS = ["psutil"]


# Handle cleanup
class ExitCleanup:
    """
    Make sure we kill child subprocesses when the main process exits receive SIGTERM.
    """

    def __init__(self):
        self._subprocesses = []
        signal.signal(signal.SIGTERM, self.exit)

    def addSubprocess(self, process):
        logging.debug(f"[ExitCleanup] Register subprocess {process}")
        self._subprocesses.append(process)

    def exit(self, signum, frame):
        for proc in self._subprocesses:
            logging.debug(f"[ExitCleanup] Kill subprocess {proc}")
            try:
                if proc.is_running():
                    proc.terminate()
                    proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

exitCleanup = ExitCleanup()


class MrNodeType(enum.Enum):
    NONE = enum.auto()
    BASENODE = enum.auto()
    NODE = enum.auto()
    COMMANDLINE = enum.auto()
    INPUT = enum.auto()
    BACKDROP = enum.auto()


class InternalAttributesFactory:
    BASIC = [
        StringParam(
            name="comment",
            label="Comments",
            description="User comments describing this specific node instance.\n"
                        "It is displayed in regular font in the invalidation/comment messages "
                        "tooltip.",
            value="",
            semantic="multiline",
            invalidate=False,
        ),
        StringParam(
            name="label",
            label="Node's Label",
            description="Customize the default label (to replace the technical name of the node "
                        "instance).",
            value="",
            invalidate=False,
        ),
        ChoiceParam(
            name="nodeDefaultLogLevel",
            label="Default Logging Level",
            description="Default logging level for the node (critical, error, warning, info, debug).",
            value="info",
            values=VERBOSE_LEVEL,
            invalidate=False,
        ),
        ColorParam(
            name="color",
            label="Color",
            description="Custom color for the node (SVG name or hexadecimal code).",
            value=lambda node: getattr(node.nodeDesc, "color", ""),
            invalidate=False,
        )
    ]

    INVALIDATION = [
        StringParam(
            name="invalidation",
            label="Invalidation Message",
            description="A message that will invalidate the node's output folder.\n"
                        "This is useful for development, we can invalidate the output of the node "
                        "when we modify the code.\n"
                        "It is displayed in bold font in the invalidation/comment messages "
                        "tooltip.",
            value="",
            semantic="multiline",
            advanced=True,
            uidIgnoreValue="",  # If the invalidation string is empty, it does not participate to the node's UID
        ),
    ]

    RESIZABLE = [
        IntParam(
            name="fontSize",
            label="Font Size",
            description="Size of the font used to display the comments.",
            value=12,
            range=(6, 100, 1),
            invalidate=False,
        ),
        ColorParam(
            name="fontColor",
            label="Font Color",
            description="Color of the font used to display the comments (SVG name or hexadecimal code).",
            value="",
            invalidate=False,
        ),
        IntParam(
            name="nodeWidth",
            label="Node Width",
            description="Width of the node in the graph editor.",
            value=600,
            range=None,
            invalidate=False,
            enabled=False,  # Hidden
        ),
        IntParam(
            name="nodeHeight",
            label="Node Height",
            description="Height of the node in the graph editor.",
            value=400,
            range=None,
            invalidate=False,
            enabled=False,  # Hidden
        ),
    ]

    @classmethod
    def getInternalAttributes(cls, mrNodeType: MrNodeType) -> list[Attribute]:
        paramMap = {
            MrNodeType.NONE: cls.BASIC,
            MrNodeType.BASENODE: cls.INVALIDATION + cls.BASIC,
            MrNodeType.NODE: cls.INVALIDATION + cls.BASIC,
            MrNodeType.COMMANDLINE: cls.INVALIDATION + cls.BASIC,
            MrNodeType.INPUT: cls.BASIC,
            MrNodeType.BACKDROP: cls.BASIC + cls.RESIZABLE,
        }

        return paramMap.get(mrNodeType)


class BaseNode(object):
    """
    """
    cpu = Level.NORMAL
    gpu = Level.NONE
    ram = Level.NORMAL
    packageName = ""
    color = ""
    _mrNodeType: MrNodeType = MrNodeType.BASENODE

    internalInputs = InternalAttributesFactory.getInternalAttributes(_mrNodeType)

    inputs = []
    outputs = []
    size = StaticNodeSize(1)
    parallelization = None
    documentation = ""
    category = "Other"
    plugin = None
    # Licenses required to run the plugin
    # Only used to select machines on the farm when the node is submitted
    _licenses = []

    def __init__(self):
        super(BaseNode, self).__init__()
        self.hasDynamicOutputAttribute = any(output.isDynamicValue for output in self.outputs)
        self.sourceCodeFolder = Path(getfile(self.__class__)).parent.resolve().as_posix()

    def getMrNodeType(self):
        return self._mrNodeType

    @classmethod
    def resolvedCpu(cls, node):
        """ Return the resolved CPU level for the given node instance.

        If `cpu` is a callable, it is called with the node instance as parameter.
        Otherwise, the static value is returned.
        """
        return cls.cpu(node) if callable(cls.cpu) else cls.cpu

    @classmethod
    def resolvedGpu(cls, node):
        """ Return the resolved GPU level for the given node instance.

        If `gpu` is a callable, it is called with the node instance as parameter.
        Otherwise, the static value is returned.
        """
        return cls.gpu(node) if callable(cls.gpu) else cls.gpu

    @classmethod
    def resolvedRam(cls, node):
        """ Return the resolved RAM level for the given node instance.

        If `ram` is a callable, it is called with the node instance as parameter.
        Otherwise, the static value is returned.
        """
        return cls.ram(node) if callable(cls.ram) else cls.ram

    @classmethod
    def resolvedSize(cls, node):
        """ Return the resolved size for the given node instance.

        If `size` is a callable, it is called with the node instance as parameter.
        If `size` is an integer, it is returned as-is.
        Objects with a `computeSize` method are supported for backward compatibility.
        """
        if callable(cls.size):
            return cls.size(node)
        if isinstance(cls.size, int):
            return cls.size
        # Backward compatibility with external size classes using computeSize instead of __call__
        if hasattr(cls.size, 'computeSize'):
            logging.warning(f"The plugin '{node.nodeType}' should use a callable instead of the deprecated method 'computeSize'.")
            return cls.size.computeSize(node)
        raise ValueError(f"{node.name} size attribute is invalid")

    def upgradeAttributeValues(self, attrValues, fromVersion):
        return attrValues

    @classmethod
    def onNodeCreated(cls, node):
        """
        Called after a node instance created from this node descriptor has been added to a Graph.
        """
        pass

    @classmethod
    def update(cls, node):
        """ Method call before node's internal update on invalidation.

        Args:
            node: the BaseNode instance being updated
        See Also:
            BaseNode.updateInternals
        """
        pass

    @classmethod
    def postUpdate(cls, node):
        """ Method call after node's internal update on invalidation.

        Args:
            node: the BaseNode instance being updated
        See Also:
            NodeBase.updateInternals
        """
        pass

    def preprocess(self, node):
        """ Gets invoked just before the processChunk method for the node.

        Args:
            node: The BaseNode instance about to be processed.
        """
        pass

    @property
    def hasPreprocess(self):
        """ Returns True if the class has a preprocess """
        return type(self).preprocess is not BaseNode.preprocess

    def postprocess(self, node):
        """ Gets invoked after the processChunk method for the node.

        Args:
            node: The BaseNode instance which is processed.
        """
        pass

    @property
    def hasPostprocess(self):
        """ Returns True if the class has a postprocess """
        return type(self).postprocess is not BaseNode.postprocess

    def process(self, node):
        raise NotImplementedError(f'No process implementation on node: "{node.name}"')

    def processChunk(self, chunk):
        if self.parallelization is None:
            self.process(chunk.node)
        else:
            raise NotImplementedError(f'No process implementation on node: "{chunk.node.name}"')

    def executeChunkCommandLine(self, chunk, cmd, env=None):
        try:
            with open(chunk.getLogFile(), 'a') as logF:
                chunk.status.commandLine = cmd
                chunk.saveStatusFile()
                cmdList = shlex.split(cmd)
                # Resolve executable to full path
                prog = shutil.which(cmdList[0], path=env.get("PATH") if env else None)

                print(f"Starting Process for '{chunk.node.name}'")
                print(f" - commandLine: {cmd}")
                print(f" - logFile: {chunk.getLogFile()}")
                if prog:
                    cmdList[0] = Path(prog).as_posix()
                    print(f" - command full path: {cmdList[0]}")

                # Change the process group to avoid Meshroom main process being killed if the
                # subprocess gets terminated by the user or an Out Of Memory (OOM kill).
                if sys.platform == "win32":
                    from subprocess import CREATE_NEW_PROCESS_GROUP
                    platformArgs = {"creationflags": CREATE_NEW_PROCESS_GROUP}
                    # Note: DETACHED_PROCESS means fully detached process.
                    # We do not want a fully detached process to ensure that if Meshroom is killed,
                    # the subprocesses are killed too.
                else:
                    platformArgs = {"start_new_session": True}
                    # Note: "preexec_fn"=os.setsid is the old way before python-3.2

                chunk.subprocess = psutil.Popen(
                    cmdList,
                    stdout=logF,
                    stderr=logF,
                    cwd=chunk.node.internalFolder,
                    env=env,
                    text=True,
                    **platformArgs,
                )
                exitCleanup.addSubprocess(chunk.subprocess)

                if hasattr(chunk, "statThread"):
                    # We only have a statThread if the node is running in the current process
                    # and not in a dedicated environment/process.
                    chunk.statThread.proc = chunk.subprocess

                stdout, stderr = chunk.subprocess.communicate()

                chunk.status.returnCode = chunk.subprocess.returncode

                if chunk.subprocess.returncode and chunk.subprocess.returncode < 0:
                    signal_num = -chunk.subprocess.returncode
                    logF.write(f"Process was killed by signal: {signal_num}")
                    try:
                        status = chunk.subprocess.status()
                        logF.write(f"Process status: {status}")
                    except Exception:
                        pass

            if chunk.subprocess.returncode != 0:
                with open(chunk.getLogFile(), "r") as logF:
                    logContent = "".join(logF.readlines())
                raise RuntimeError(f'Error on node "{chunk.name}":\nLog:\n{logContent}')
        finally:
            chunk.subprocess = None

    def stopProcess(self, chunk):
        # The same node could exists several times in the graph and
        # only one would have the running subprocess; ignore all others
        if not chunk.subprocess:
            logging.warning(f"[{chunk.node.name}] stopProcess: no subprocess")
            return

        # Retrieve process tree
        processes = chunk.subprocess.children(recursive=True) + [chunk.subprocess]
        logging.debug(f"[{chunk.node.name}] Processes to stop: {len(processes)}")
        for process in processes:
            try:
                # With terminate, the process has a chance to handle cleanup
                process.terminate()
            except psutil.NoSuchProcess:
                pass

        # If it is still running, force kill it
        for process in processes:
            try:
                # Use is_running() instead of poll() as we use a psutil.Process object
                if process.is_running():  # Check if process is still alive
                    process.kill()  # Forcefully kill it
            except psutil.NoSuchProcess:
                logging.info(f"[{chunk.node.name}] Process already terminated.")
            except psutil.AccessDenied:
                logging.info(f"[{chunk.node.name}] Permission denied to kill the process.")


class InputNode(BaseNode):
    """
    Node that does not need to be processed, it is just a placeholder for inputs.
    """
    _mrNodeType: MrNodeType = MrNodeType.INPUT
    internalInputs = InternalAttributesFactory.getInternalAttributes(_mrNodeType)

    def __init__(self):
        super(InputNode, self).__init__()

    def getMrNodeType(self):
        return self._mrNodeType

    def processChunk(self, chunk):
        pass

    def process(self, node):
        pass

class BackdropNode(BaseNode):
    """
    Node that does not need to be processed, it is just a placeholder for grouping other nodes.
    """
    _mrNodeType: MrNodeType = MrNodeType.BACKDROP
    internalInputs = InternalAttributesFactory.getInternalAttributes(_mrNodeType)

    def __init__(self):
        super(BackdropNode, self).__init__()

    def getMrNodeType(self):
        return self._mrNodeType

    def processChunk(self, chunk):
        pass

    def process(self, node):
        pass


class Node(BaseNode):
    pythonExecutable = "python"
    _mrNodeType: MrNodeType = MrNodeType.NODE

    def __init__(self):
        super(Node, self).__init__()

    def getMrNodeType(self):
        return self._mrNodeType

    def processChunkInEnvironment(self, chunk):
        meshroomComputeCmd = f"{chunk.node.nodeDesc.pythonExecutable} {_MESHROOM_COMPUTE}" + \
                             f" \"{chunk.node.graph.filepath}\" --node {chunk.node.name}" + \
                              " --extern --inCurrentEnv"
        if chunk.isPreprocess:
            meshroomComputeCmd += f" --preprocess"
        elif chunk.isPostprocess:
            meshroomComputeCmd += f" --postprocess"
        elif len(chunk.node.getChunks()) >= 1:
            meshroomComputeCmd += f" --iteration {chunk.range.iteration}"

        runtimeEnv = chunk.node.nodeDesc.plugin.runtimeEnv
        cmdPrefix = chunk.node.nodeDesc.plugin.commandPrefix
        cmdSuffix = chunk.node.nodeDesc.plugin.commandSuffix
        self.executeChunkCommandLine(chunk, cmdPrefix + meshroomComputeCmd + cmdSuffix,
                                     env=runtimeEnv)


class CommandLineNode(BaseNode):
    """
    """
    commandLine = ""  # need to be defined on the node
    parallelization = None
    commandLineRange = ""
    _mrNodeType: MrNodeType = MrNodeType.COMMANDLINE

    def __init__(self):
        super(CommandLineNode, self).__init__()

    def getMrNodeType(self):
        return self._mrNodeType

    def buildCommandLine(self, chunk) -> str:
        cmdLineVars = chunk.node.createCmdLineVars()
        cmdPrefix = ""
        cmdSuffix = ""
        if chunk.node.nodeDesc.plugin:
            cmdPrefix = chunk.node.nodeDesc.plugin.commandPrefix
            cmdSuffix = chunk.node.nodeDesc.plugin.commandSuffix
        if chunk.node.isParallelized and chunk.node.size > 1:
            cmdSuffix = " " + self.commandLineRange.format(**chunk.range.toDict()) + " " + cmdSuffix

        # In the case of a lambda, we want a single "node" argument and not the node descriptor "self".
        # Therefore, we use getattr_static to retrieve the raw lambda instead of a bound method, which
        # would impose "self" as the first argument if we accessed "self.commandLine".
        commandLineValue = getattr_static(self, 'commandLine')
        if callable(commandLineValue):
            cmd = commandLineValue(chunk.node)
        else:
            cmd = commandLineValue.format(**chunk.node._expVars, **chunk.node._staticExpVars, **cmdLineVars)
        return cmdPrefix + cmd + cmdSuffix

    def processChunk(self, chunk):
        cmd = self.buildCommandLine(chunk)
        runtimeEnv = chunk.node.nodeDesc.plugin.runtimeEnv
        self.executeChunkCommandLine(chunk, cmd, env=runtimeEnv)


# Specific command line node for AliceVision apps
class AVCommandLineNode(CommandLineNode):

    cgroupParsed = False
    cmdMem = ""
    cmdCore = ""

    def __init__(self):
        super(AVCommandLineNode, self).__init__()

        if AVCommandLineNode.cgroupParsed is False:

            AVCommandLineNode.cmdMem = ""
            memSize = cgroup.getCgroupMemorySize()
            if memSize > 0:
                AVCommandLineNode.cmdMem = f" --maxMemory={memSize}"

            AVCommandLineNode.cmdCore = ""
            coresCount = cgroup.getCgroupCpuCount()
            if coresCount > 0:
                AVCommandLineNode.cmdCore = f" --maxCores={coresCount}"

            AVCommandLineNode.cgroupParsed = True

    def buildCommandLine(self, chunk) -> str:
        commandLineString = super(AVCommandLineNode, self).buildCommandLine(chunk)

        return commandLineString + AVCommandLineNode.cmdMem + AVCommandLineNode.cmdCore


class InitNode(object):
    def __init__(self):
        super(InitNode, self).__init__()

    def initialize(self, node, inputs, recursiveInputs):
        """
        Initialize the attributes that are needed for a node to start running.

        Args:
            node (Node): the node whose attributes must be initialized
            inputs (list): the user-provided list of input files/directories
            recursiveInputs (list): the user-provided list of input directories to search
                                    recursively for images
        """
        pass

    def resetAttributes(self, node, attributeNames):
        """
        Reset the values of the provided attributes for a node.

        Args:
            node (Node): the node whose attributes are to be reset
            attributeNames (list): the list containing the names of the attributes to reset
        """
        for attrName in attributeNames:
            if node.hasAttribute(attrName):
                node.attribute(attrName).resetToDefaultValue()

    def extendAttributes(self, node, attributesDict):
        """
        Extend the values of the provided attributes for a node.

        Args:
            node (Node): the node whose attributes are to be extended
            attributesDict (dict): the dictionary containing the attributes' names (as keys) and the
                                   values to extend with
        """
        for attr in attributesDict.keys():
            if node.hasAttribute(attr):
                node.attribute(attr).extend(attributesDict[attr])

    def setAttributes(self, node, attributesDict):
        """
        Set the values of the provided attributes for a node.

        Args:
            node (Node): the node whose attributes are to be extended
            attributesDict (dict): the dictionary containing the attributes' names (as keys) and the
                                   values to set
        """
        for attr in attributesDict:
            if node.hasAttribute(attr):
                node.attribute(attr).value = attributesDict[attr]
