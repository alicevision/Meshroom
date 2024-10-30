import os
import psutil
import shlex

from .computation import Level, StaticNodeSize
from .attribute import StringParam, ColorParam

from meshroom.core import cgroup


class Node(object):
    """
    """
    internalFolder = '{cache}/{nodeType}/{uid}/'
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
        super(Node, self).__init__()
        self.hasDynamicOutputAttribute = any(output.isDynamicValue for output in self.outputs)

    def upgradeAttributeValues(self, attrValues, fromVersion):
        return attrValues

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

    def stopProcess(self, chunk):
        raise NotImplementedError('No stopProcess implementation on node: {}'.format(chunk.node.name))

    def processChunk(self, chunk):
        raise NotImplementedError('No processChunk implementation on node: "{}"'.format(chunk.node.name))


class InputNode(Node):
    """
    Node that does not need to be processed, it is just a placeholder for inputs.
    """
    def __init__(self):
        super(InputNode, self).__init__()

    def processChunk(self, chunk):
        pass


class CommandLineNode(Node):
    """
    """
    commandLine = ''  # need to be defined on the node
    parallelization = None
    commandLineRange = ''

    def __init__(self):
        super(CommandLineNode, self).__init__()

    def buildCommandLine(self, chunk):

        cmdPrefix = ''
        # If rez available in env, we use it
        if "REZ_ENV" in os.environ and chunk.node.packageVersion:
            # If the node package is already in the environment, we don't need a new dedicated rez environment
            alreadyInEnv = os.environ.get("REZ_{}_VERSION".format(chunk.node.packageName.upper()),
                                          "").startswith(chunk.node.packageVersion)
            if not alreadyInEnv:
                cmdPrefix = '{rez} {packageFullName} -- '.format(rez=os.environ.get("REZ_ENV"),
                                                                 packageFullName=chunk.node.packageFullName)

        cmdSuffix = ''
        if chunk.node.isParallelized and chunk.node.size > 1:
            cmdSuffix = ' ' + self.commandLineRange.format(**chunk.range.toDict())

        return cmdPrefix + chunk.node.nodeDesc.commandLine.format(**chunk.node._cmdVars) + cmdSuffix

    def stopProcess(self, chunk):
        # The same node could exists several times in the graph and
        # only one would have the running subprocess; ignore all others
        if not hasattr(chunk, "subprocess"):
            return
        if chunk.subprocess:
            # Kill process tree
            processes = chunk.subprocess.children(recursive=True) + [chunk.subprocess]
            try:
                for process in processes:
                    process.terminate()
            except psutil.NoSuchProcess:
                pass

    def processChunk(self, chunk):
        try:
            with open(chunk.logFile, 'w') as logF:
                cmd = self.buildCommandLine(chunk)
                chunk.status.commandLine = cmd
                chunk.saveStatusFile()
                print(' - commandLine: {}'.format(cmd))
                print(' - logFile: {}'.format(chunk.logFile))
                chunk.subprocess = psutil.Popen(shlex.split(cmd), stdout=logF, stderr=logF, cwd=chunk.node.internalFolder)

                # Store process static info into the status file
                # chunk.status.env = node.proc.environ()
                # chunk.status.createTime = node.proc.create_time()

                chunk.statThread.proc = chunk.subprocess
                stdout, stderr = chunk.subprocess.communicate()
                chunk.subprocess.wait()

                chunk.status.returnCode = chunk.subprocess.returncode

            if chunk.subprocess.returncode != 0:
                with open(chunk.logFile, 'r') as logF:
                    logContent = ''.join(logF.readlines())
                raise RuntimeError('Error on node "{}":\nLog:\n{}'.format(chunk.name, logContent))
        except Exception:
            raise
        finally:
            chunk.subprocess = None


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
                AVCommandLineNode.cmdMem = ' --maxMemory={memSize}'.format(memSize=memSize)

            AVCommandLineNode.cmdCore = ''
            coresCount = cgroup.getCgroupCpuCount()
            if coresCount > 0:
                AVCommandLineNode.cmdCore = ' --maxCores={coresCount}'.format(coresCount=coresCount)

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
            recursiveInputs (list): the user-provided list of input directories to search recursively for images
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
            attributesDict (dict): the dictionary containing the attributes' names (as keys) and the values to extend with
        """
        for attr in attributesDict.keys():
            if node.hasAttribute(attr):
                node.attribute(attr).extend(attributesDict[attr])

    def setAttributes(self, node, attributesDict):
        """
        Set the values of the provided attributes for a node.

        Args:
            node (Node): the node whose attributes are to be extended
            attributesDict (dict): the dictionary containing the attributes' names (as keys) and the values to set
        """
        for attr in attributesDict:
            if node.hasAttribute(attr):
                node.attribute(attr).value = attributesDict[attr]
