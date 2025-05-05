import enum
from inspect import getfile
from pathlib import Path
import logging
import os
import psutil
import shlex
import shutil
import sys

from .computation import Level, StaticNodeSize
from .attribute import StringParam, ColorParam

import meshroom
from meshroom.core import cgroup

_MESHROOM_ROOT = Path(meshroom.__file__).parent.parent
_MESHROOM_COMPUTE = _MESHROOM_ROOT / "bin" / "meshroom_compute"


class MrNodeType(enum.Enum):
    NONE = enum.auto()
    BASENODE = enum.auto()
    NODE = enum.auto()
    COMMANDLINE = enum.auto()
    INPUT = enum.auto()


class BaseNode(object):
    """
    """
    cpu = Level.NORMAL
    gpu = Level.NONE
    ram = Level.NORMAL
    packageName = ''
    packageVersion = ''
    internalInputs = [
        StringParam(
            name="invalidation",
            label="Invalidation Message",
            description="A message that will invalidate the node's output folder.\n"
                        "This is useful for development, we can invalidate the output of the node when we modify the code.\n"
                        "It is displayed in bold font in the invalidation/comment messages tooltip.",
            value="",
            semantic="multiline",
            advanced=True,
            uidIgnoreValue="",  # If the invalidation string is empty, it does not participate to the node's UID
        ),
        StringParam(
            name="comment",
            label="Comments",
            description="User comments describing this specific node instance.\n"
                        "It is displayed in regular font in the invalidation/comment messages tooltip.",
            value="",
            semantic="multiline",
            invalidate=False,
        ),
        StringParam(
            name="label",
            label="Node's Label",
            description="Customize the default label (to replace the technical name of the node instance).",
            value="",
            invalidate=False,
        ),
        ColorParam(
            name="color",
            label="Color",
            description="Custom color for the node (SVG name or hexadecimal code).",
            value="",
            invalidate=False,
        )
    ]
    inputs = []
    outputs = []
    size = StaticNodeSize(1)
    parallelization = None
    documentation = ''
    category = 'Other'

    def __init__(self):
        super(BaseNode, self).__init__()
        self.hasDynamicOutputAttribute = any(output.isDynamicValue for output in self.outputs)
        self.sourceCodeFolder = Path(getfile(self.__class__)).parent.resolve().as_posix()

    def getMrNodeType(self):
        return MrNodeType.BASENODE

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

    def postprocess(self, node):
        """ Gets invoked after the processChunk method for the node.

        Args:
            node: The BaseNode instance which is processed.
        """
        pass

    def processChunk(self, chunk):
        raise NotImplementedError(f'No processChunk implementation on node: "{chunk.node.name}"')

    def executeChunkCommandLine(self, chunk, cmd, env=None):
        try:
            with open(chunk.logFile, 'w') as logF:
                chunk.status.commandLine = cmd
                chunk.saveStatusFile()
                cmdList = shlex.split(cmd)
                # Resolve executable to full path
                prog = shutil.which(cmdList[0], path=env.get('PATH') if env else None)

                print(f"Starting Process for '{chunk.node.name}'")
                print(f' - commandLine: {cmd}')
                print(f' - logFile: {chunk.logFile}')
                if prog:
                    cmdList[0] = prog
                    print(f' - command full path: {prog}')

                # Change the process group to avoid Meshroom main process being killed if the
                # subprocess gets terminated by the user or an Out Of Memory (OOM kill).
                if sys.platform == "win32":
                    from subprocess import CREATE_NEW_PROCESS_GROUP
                    platformArgs = {"creationflags": CREATE_NEW_PROCESS_GROUP}
                    # Note: DETACHED_PROCESS means fully detached process.
                    # We don't want a fully detached process to ensure that if Meshroom is killed,
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
                    **platformArgs,
                )

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
                with open(chunk.logFile, 'r') as logF:
                    logContent = ''.join(logF.readlines())
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
    def __init__(self):
        super(InputNode, self).__init__()

    def getMrNodeType(self):
        return MrNodeType.INPUT

    def processChunk(self, chunk):
        pass


class Node(BaseNode):

    def __init__(self):
        super(Node, self).__init__()

    def getMrNodeType(self):
        return MrNodeType.NODE

    def processChunkInEnvironment(self, chunk):
        meshroomComputeCmd = f"python {_MESHROOM_COMPUTE} {chunk.node.graph.filepath} --node {chunk.node.name} --extern --inCurrentEnv"
        if len(chunk.node.getChunks()) > 1:
            meshroomComputeCmd += f" --iteration {chunk.range.iteration}"

        runtimeEnv = None
        self.executeChunkCommandLine(chunk, meshroomComputeCmd, env=runtimeEnv)


class CommandLineNode(BaseNode):
    """
    """
    commandLine = ''  # need to be defined on the node
    parallelization = None
    commandLineRange = ''

    def __init__(self):
        super(CommandLineNode, self).__init__()

    def getMrNodeType(self):
        return MrNodeType.COMMANDLINE

    def buildCommandLine(self, chunk):
        cmdPrefix = ''
        cmdSuffix = ''
        if chunk.node.isParallelized and chunk.node.size > 1:
            cmdSuffix = ' ' + self.commandLineRange.format(**chunk.range.toDict())

        return cmdPrefix + chunk.node.nodeDesc.commandLine.format(**chunk.node._cmdVars) + cmdSuffix

    def processChunk(self, chunk):
        cmd = self.buildCommandLine(chunk)
        # TODO: Setup runtime env
        self.executeChunkCommandLine(chunk, cmd)


# Specific command line node for AliceVision apps
class AVCommandLineNode(CommandLineNode):

    cgroupParsed = False
    cmdMem = ''
    cmdCore = ''

    def __init__(self):
        super(AVCommandLineNode, self).__init__()

        if AVCommandLineNode.cgroupParsed is False:

            AVCommandLineNode.cmdMem = ''
            memSize = cgroup.getCgroupMemorySize()
            if memSize > 0:
                AVCommandLineNode.cmdMem = f' --maxMemory={memSize}'

            AVCommandLineNode.cmdCore = ''
            coresCount = cgroup.getCgroupCpuCount()
            if coresCount > 0:
                AVCommandLineNode.cmdCore = f' --maxCores={coresCount}'

            AVCommandLineNode.cgroupParsed = True

    def buildCommandLine(self, chunk):
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
