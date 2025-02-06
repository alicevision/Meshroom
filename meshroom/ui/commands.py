import logging
import traceback
from contextlib import contextmanager

from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtCore import Property, Signal

from meshroom.core.attribute import ListAttribute, Attribute
from meshroom.core.graph import GraphModification
from meshroom.core.node import Position
from meshroom.core.nodeFactory import nodeFactory


class UndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        super(UndoCommand, self).__init__(parent)
        self._enabled = True

    def setEnabled(self, enabled):
        self._enabled = enabled

    def redo(self):
        if not self._enabled:
            return
        try:
            self.redoImpl()
        except Exception:
            logging.error("Error while redoing command '{}': \n{}".format(self.text(), traceback.format_exc()))

    def undo(self):
        if not self._enabled:
            return
        try:
            self.undoImpl()
        except Exception:
            logging.error("Error while undoing command '{}': \n{}".format(self.text(), traceback.format_exc()))

    def redoImpl(self):
        # type: () -> bool
        pass

    def undoImpl(self):
        # type: () -> bool
        pass


class UndoStack(QUndoStack):
    def __init__(self, parent=None):
        super(UndoStack, self).__init__(parent)
        # connect QUndoStack signal to UndoStack's ones
        self.cleanChanged.connect(self._cleanChanged)
        self.canUndoChanged.connect(self._canUndoChanged)
        self.canRedoChanged.connect(self._canRedoChanged)
        self.undoTextChanged.connect(self._undoTextChanged)
        self.redoTextChanged.connect(self._redoTextChanged)
        self.indexChanged.connect(self._indexChanged)

        self._undoableIndex = 0  # used to block the undo stack while computing
        self._lockedRedo = False  # used to avoid unwanted behaviors while computing

    def tryAndPush(self, command):
        # type: (UndoCommand) -> bool
        try:
            res = command.redoImpl()
        except Exception as e:
            logging.error("Error while trying command '{}': \n{}".format(command.text(), traceback.format_exc()))
            res = False
        if res is not False:
            command.setEnabled(False)
            self.push(command)  # takes ownership
            self.setLockedRedo(False)  # make sure to unlock the redo action
            command.setEnabled(True)
        return res

    def setUndoableIndex(self, value):
        if self._undoableIndex == value:
            return
        self._undoableIndex = value
        self.isUndoableIndexChanged.emit()

    def setLockedRedo(self, value):
        if self._lockedRedo == value:
            return
        self._lockedRedo = value
        self.lockedRedoChanged.emit()

    def lockAtThisIndex(self):
        """
        Lock the undo stack at the current index and lock the redo action.
        Note: should be used while starting a new compute to avoid problems.
        """
        self.setUndoableIndex(self.index)
        self.setLockedRedo(True)

    def unlock(self):
        """ Unlock both undo stack and redo action. """
        self.setUndoableIndex(0)
        self.setLockedRedo(False)

    # Redeclare QUndoStack signal since original ones can not be used for properties notifying
    _cleanChanged = Signal()
    _canUndoChanged = Signal()
    _canRedoChanged = Signal()
    _undoTextChanged = Signal()
    _redoTextChanged = Signal()
    _indexChanged = Signal()

    clean = Property(bool, QUndoStack.isClean, notify=_cleanChanged)
    canUndo = Property(bool, QUndoStack.canUndo, notify=_canRedoChanged)
    canRedo = Property(bool, QUndoStack.canRedo, notify=_canUndoChanged)
    undoText = Property(str, QUndoStack.undoText, notify=_undoTextChanged)
    redoText = Property(str, QUndoStack.redoText, notify=_redoTextChanged)
    index = Property(int, QUndoStack.index, notify=_indexChanged)

    isUndoableIndexChanged = Signal()
    isUndoableIndex = Property(bool, lambda self: self.index > self._undoableIndex, notify=isUndoableIndexChanged)
    lockedRedoChanged = Signal()
    lockedRedo = Property(bool, lambda self: self._lockedRedo, setLockedRedo, notify=lockedRedoChanged)


class GraphCommand(UndoCommand):
    def __init__(self, graph, parent=None):
        super(GraphCommand, self).__init__(parent)
        self.graph = graph


class AddNodeCommand(GraphCommand):
    def __init__(self, graph, nodeType, position, parent=None, **kwargs):
        super(AddNodeCommand, self).__init__(graph, parent)
        self.nodeType = nodeType
        self.nodeName = None
        self.position = position
        self.kwargs = kwargs
        # Serialize Attributes as link expressions
        for key, value in self.kwargs.items():
            if isinstance(value, Attribute):
                self.kwargs[key] = value.asLinkExpr()
            elif isinstance(value, list):
                for idx, v in enumerate(value):
                    if isinstance(v, Attribute):
                         value[idx] = v.asLinkExpr()

    def redoImpl(self):
        node = self.graph.addNewNode(self.nodeType, position=self.position, **self.kwargs)
        self.nodeName = node.name
        self.setText("Add Node {}".format(self.nodeName))
        return node

    def undoImpl(self):
        self.graph.removeNode(self.nodeName)


class RemoveNodeCommand(GraphCommand):
    def __init__(self, graph, node, parent=None):
        super(RemoveNodeCommand, self).__init__(graph, parent)
        self.nodeDict = node.toDict()
        self.nodeName = node.getName()
        self.setText("Remove Node {}".format(self.nodeName))
        self.outEdges = {}
        self.outListAttributes = {}  # maps attribute's key with a tuple containing the name of the list it is connected to and its value

    def redoImpl(self):
        # keep outEdges (inEdges are serialized in nodeDict so unneeded here) and outListAttributes to be able to recreate the deleted elements in ListAttributes
        _, self.outEdges, self.outListAttributes = self.graph.removeNode(self.nodeName)
        return True

    def undoImpl(self):
        with GraphModification(self.graph):
            node = nodeFactory(self.nodeDict, self.nodeName)
            self.graph.addNode(node, self.nodeName)
            assert (node.getName() == self.nodeName)
            # recreate out edges deleted on node removal
            for dstAttr, srcAttr in self.outEdges.items():
                # if edges were connected to ListAttributes, recreate their corresponding entry in said ListAttribute
                # 0 = attribute name, 1 = attribute index, 2 = attribute value
                if dstAttr in self.outListAttributes.keys():
                    listAttr = self.graph.attribute(self.outListAttributes[dstAttr][0])
                    if isinstance(self.outListAttributes[dstAttr][2], list):
                        listAttr[self.outListAttributes[dstAttr][1]:self.outListAttributes[dstAttr][1]] = self.outListAttributes[dstAttr][2]
                    else:
                        listAttr.insert(self.outListAttributes[dstAttr][1], self.outListAttributes[dstAttr][2])

                self.graph.addEdge(self.graph.attribute(srcAttr),
                                   self.graph.attribute(dstAttr))


class DuplicateNodesCommand(GraphCommand):
    """
    Handle node duplication in a Graph.
    """
    def __init__(self, graph, srcNodes, parent=None):
        super(DuplicateNodesCommand, self).__init__(graph, parent)
        self.srcNodeNames = [ n.name for n in srcNodes ]
        self.setText("Duplicate Nodes")

    def redoImpl(self):
        srcNodes = [ self.graph.node(i) for i in self.srcNodeNames ]
        # flatten the list of duplicated nodes to avoid lists within the list
        duplicates = [ n for nodes in list(self.graph.duplicateNodes(srcNodes).values()) for n in nodes ]
        self.duplicates = [ n.name for n in duplicates ]
        return duplicates

    def undoImpl(self):
        # remove all duplicates
        for duplicate in self.duplicates:
            self.graph.removeNode(duplicate)


class PasteNodesCommand(GraphCommand):
    """
    Handle node pasting in a Graph.
    """
    def __init__(self, graph, data, position=None, parent=None):
        super(PasteNodesCommand, self).__init__(graph, parent)
        self.data = data
        self.position = position
        self.nodeNames = []

    def redoImpl(self):
        data = self.graph.updateImportedProject(self.data)
        nodes = self.graph.pasteNodes(data, self.position)
        self.nodeNames = [node.name for node in nodes]
        self.setText("Paste Node{} ({})".format("s" if len(self.nodeNames) > 1 else "", ", ".join(self.nodeNames)))
        return nodes

    def undoImpl(self):
        for name in self.nodeNames:
            self.graph.removeNode(name)


class ImportProjectCommand(GraphCommand):
    """
    Handle the import of a project into a Graph.
    """
    def __init__(self, graph, filepath=None, position=None, yOffset=0, parent=None):
        super(ImportProjectCommand, self).__init__(graph, parent)
        self.filepath = filepath
        self.importedNames = []
        self.position = position
        self.yOffset = yOffset

    def redoImpl(self):
        status = self.graph.load(self.filepath, setupProjectFile=False, importProject=True)
        importedNodes = self.graph.importedNodes
        self.setText("Import Project ({} nodes)".format(importedNodes.count))

        lowestY = 0
        for node in self.graph.nodes:
            if node not in importedNodes and node.y > lowestY:
                lowestY = node.y

        for node in importedNodes:
            self.importedNames.append(node.name)
            if self.position is not None:
                self.graph.node(node.name).position = Position(node.x + self.position.x, node.y + self.position.y)
            else:
                self.graph.node(node.name).position = Position(node.x, node.y + lowestY + self.yOffset)

        return importedNodes

    def undoImpl(self):
        for nodeName in self.importedNames:
            self.graph.removeNode(nodeName)
        self.importedNames = []


class SetAttributeCommand(GraphCommand):
    def __init__(self, graph, attribute, value, parent=None):
        super(SetAttributeCommand, self).__init__(graph, parent)
        self.attrName = attribute.getFullNameToNode()
        self.value = value
        self.oldValue = attribute.getExportValue()
        self.setText("Set Attribute '{}'".format(attribute.getFullNameToNode()))

    def redoImpl(self):
        if self.value == self.oldValue:
            return False
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).value = self.value
        else:
            self.graph.internalAttribute(self.attrName).value = self.value
        return True

    def undoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).value = self.oldValue
        else:
            self.graph.internalAttribute(self.attrName).value = self.oldValue


class AddEdgeCommand(GraphCommand):
    def __init__(self, graph, src, dst, parent=None):
        super(AddEdgeCommand, self).__init__(graph, parent)
        self.srcAttr = src.getFullNameToNode()
        self.dstAttr = dst.getFullNameToNode()
        self.setText("Connect '{}'->'{}'".format(self.srcAttr, self.dstAttr))

        if src.baseType != dst.baseType:
            raise ValueError("Attribute types are not compatible and cannot be connected: '{}'({})->'{}'({})".format(self.srcAttr, src.baseType, self.dstAttr, dst.baseType))

    def redoImpl(self):
        self.graph.addEdge(self.graph.attribute(self.srcAttr), self.graph.attribute(self.dstAttr))
        return True

    def undoImpl(self):
        self.graph.removeEdge(self.graph.attribute(self.dstAttr))


class RemoveEdgeCommand(GraphCommand):
    def __init__(self, graph, edge, parent=None):
        super(RemoveEdgeCommand, self).__init__(graph, parent)
        self.srcAttr = edge.src.getFullNameToNode()
        self.dstAttr = edge.dst.getFullNameToNode()
        self.setText("Disconnect '{}'->'{}'".format(self.srcAttr, self.dstAttr))

    def redoImpl(self):
        self.graph.removeEdge(self.graph.attribute(self.dstAttr))
        return True

    def undoImpl(self):
        self.graph.addEdge(self.graph.attribute(self.srcAttr),
                           self.graph.attribute(self.dstAttr))


class ListAttributeAppendCommand(GraphCommand):
    def __init__(self, graph, listAttribute, value, parent=None):
        super(ListAttributeAppendCommand, self).__init__(graph, parent)
        assert isinstance(listAttribute, ListAttribute)
        self.attrName = listAttribute.getFullNameToNode()
        self.index = None
        self.count = 1
        self.value = value if value else None
        self.setText("Append to {}".format(self.attrName))

    def redoImpl(self):
        listAttribute = self.graph.attribute(self.attrName)
        self.index = len(listAttribute)
        if isinstance(self.value, list):
            listAttribute.extend(self.value)
            self.count = len(self.value)
        else:
            listAttribute.append(self.value)
        return True

    def undoImpl(self):
        listAttribute = self.graph.attribute(self.attrName)
        listAttribute.remove(self.index, self.count)


class ListAttributeRemoveCommand(GraphCommand):
    def __init__(self, graph, attribute, parent=None):
        super(ListAttributeRemoveCommand, self).__init__(graph, parent)
        listAttribute = attribute.root
        assert isinstance(listAttribute, ListAttribute)
        self.listAttrName = listAttribute.getFullNameToNode()
        self.index = listAttribute.index(attribute)
        self.value = attribute.getExportValue()
        self.setText("Remove {}".format(attribute.getFullNameToNode()))

    def redoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.remove(self.index)
        return True

    def undoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.insert(self.index, self.value)


class RemoveImagesCommand(GraphCommand):
    def __init__(self, graph, cameraInitNodes, parent=None):
        super(RemoveImagesCommand, self).__init__(graph, parent)
        self.cameraInits = cameraInitNodes
        self.viewpoints = { cameraInit.name: cameraInit.attribute("viewpoints").getExportValue() for cameraInit in self.cameraInits }
        self.intrinsics = { cameraInit.name: cameraInit.attribute("intrinsics").getExportValue() for cameraInit in self.cameraInits }
        self.title = "Remove{}Images".format(" " if len(self.cameraInits) == 1 else " All ")
        self.setText(self.title)

    def redoImpl(self):
        for i in range(len(self.cameraInits)):
            # Reset viewpoints
            self.cameraInits[i].viewpoints.resetToDefaultValue()
            self.cameraInits[i].viewpoints.valueChanged.emit()
            self.cameraInits[i].viewpoints.requestGraphUpdate()

            # Reset intrinsics
            self.cameraInits[i].intrinsics.resetToDefaultValue()
            self.cameraInits[i].intrinsics.valueChanged.emit()
            self.cameraInits[i].intrinsics.requestGraphUpdate()

    def undoImpl(self):
        for cameraInit in self.viewpoints:
            with GraphModification(self.graph):
                self.graph.node(cameraInit).viewpoints.value = self.viewpoints[cameraInit]
                self.graph.node(cameraInit).intrinsics.value = self.intrinsics[cameraInit]


class MoveNodeCommand(GraphCommand):
    """ Move a node to a given position. """
    def __init__(self, graph, node, position, parent=None):
        super(MoveNodeCommand, self).__init__(graph, parent)
        self.nodeName = node.name
        self.oldPosition = node.position
        self.newPosition = position
        self.setText("Move {}".format(self.nodeName))

    def redoImpl(self):
        self.graph.node(self.nodeName).position = self.newPosition
        return True

    def undoImpl(self):
        self.graph.node(self.nodeName).position = self.oldPosition


class UpgradeNodeCommand(GraphCommand):
    """
    Perform node upgrade on a CompatibilityNode.
    """
    def __init__(self, graph, node, parent=None):
        super(UpgradeNodeCommand, self).__init__(graph, parent)
        self.nodeDict = node.toDict()
        self.nodeName = node.getName()
        self.outEdges = {}
        self.outListAttributes = {}
        self.setText("Upgrade Node {}".format(self.nodeName))

    def redoImpl(self):
        if not self.graph.node(self.nodeName).canUpgrade:
            return False
        upgradedNode, _, self.outEdges, self.outListAttributes = self.graph.upgradeNode(self.nodeName)
        return upgradedNode

    def undoImpl(self):
        # delete upgraded node
        expectedUid = self.graph.node(self.nodeName)._uid
        self.graph.removeNode(self.nodeName)
        # recreate compatibility node
        with GraphModification(self.graph):
            # We come back from an upgrade, so we enforce uidConflict=True as there was a uid conflict before
            node = nodeFactory(self.nodeDict, name=self.nodeName, expectedUid=expectedUid)
            self.graph.addNode(node, self.nodeName)
            # recreate out edges
            for dstAttr, srcAttr in self.outEdges.items():
                # if edges were connected to ListAttributes, recreate their corresponding entry in said ListAttribute
                # 0 = attribute name, 1 = attribute index, 2 = attribute value
                if dstAttr in self.outListAttributes.keys():
                    listAttr = self.graph.attribute(self.outListAttributes[dstAttr][0])
                    if isinstance(self.outListAttributes[dstAttr][2], list):
                        listAttr[self.outListAttributes[dstAttr][1]:self.outListAttributes[dstAttr][1]] = self.outListAttributes[dstAttr][2]
                    else:
                        listAttr.insert(self.outListAttributes[dstAttr][1], self.outListAttributes[dstAttr][2])

                self.graph.addEdge(self.graph.attribute(srcAttr),
                                   self.graph.attribute(dstAttr))


class EnableGraphUpdateCommand(GraphCommand):
    """ Command to enable/disable graph update.
    Should not be used directly, use GroupedGraphModification context manager instead.
    """
    def __init__(self, graph, enabled, parent=None):
        super(EnableGraphUpdateCommand, self).__init__(graph, parent)
        self.enabled = enabled
        self.previousState = self.graph.updateEnabled

    def redoImpl(self):
        self.graph.updateEnabled = self.enabled
        return True

    def undoImpl(self):
        self.graph.updateEnabled = self.previousState


@contextmanager
def GroupedGraphModification(graph, undoStack, title, disableUpdates=True):
    """ A context manager that creates a macro command disabling (if not already) graph update by default
    and resetting its status after nested block execution.

    Args:
        graph (Graph): the Graph that will be modified
        undoStack (UndoStack): the UndoStack to work with
        title (str): the title of the macro command
        disableUpdates (bool): whether to disable graph updates
    """
    # Store graph update state
    state = graph.updateEnabled
    # Create a new command macro and push a command that disable graph updates
    undoStack.beginMacro(title)
    if disableUpdates:
        undoStack.tryAndPush(EnableGraphUpdateCommand(graph, False))
    try:
        yield  # Execute nested block
    except Exception:
        raise
    finally:
        if disableUpdates:
            # Push a command restoring graph update state and end command macro
            undoStack.tryAndPush(EnableGraphUpdateCommand(graph, state))
        undoStack.endMacro()
