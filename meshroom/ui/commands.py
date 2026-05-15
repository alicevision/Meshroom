import logging
import traceback
from contextlib import contextmanager

from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtCore import Property, Signal

from meshroom.core.attribute import ListAttribute, Attribute
from meshroom.core.exception import CyclicDependencyError,InvalidEdgeError
from meshroom.core.graph import Graph, GraphModification
from meshroom.core.node import Position, CompatibilityIssue
from meshroom.core.nodeFactory import nodeFactory
from meshroom.core.mtyping import PathLike


class UndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True

    def setEnabled(self, enabled):
        self._enabled = enabled

    def redo(self):
        if not self._enabled:
            return
        try:
            self.redoImpl()
        except Exception:
            logging.error(f"Error while redoing command '{self.text()}': \n{traceback.format_exc()}")

    def undo(self):
        if not self._enabled:
            return
        try:
            self.undoImpl()
        except Exception:
            logging.error(f"Error while undoing command '{self.text()}': \n{traceback.format_exc()}")

    def redoImpl(self):
        # type: () -> bool
        pass

    def undoImpl(self):
        # type: () -> bool
        pass


class UndoStack(QUndoStack):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        except Exception:
            logging.error(f"Error while trying command '{command.text()}': \n{traceback.format_exc()}")
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
        super().__init__(parent)
        self.graph = graph


class AddNodeCommand(GraphCommand):
    def __init__(self, graph, nodeType, position, parent=None, **kwargs):
        super().__init__(graph, parent)
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
        self.setText(f"Add Node {self.nodeName}")
        return node

    def undoImpl(self):
        self.graph.removeNode(self.nodeName)


class RenameNodeCommand(GraphCommand):
    def __init__(self, graph, node, name, parent=None):
        """ Command to rename a node. The new name should not be used yet.
        """
        super().__init__(graph, parent)
        self.node = node
        self.oldName = node._name
        self.name = name

    def redoImpl(self):
        self.setText(f"Rename Node {self.oldName} to {self.name}")
        self.graph.renameNode(self.node, self.name)
        return self.node._name

    def undoImpl(self):
        self.graph.renameNode(self.node, self.oldName)


class RemoveNodeCommand(GraphCommand):
    def __init__(self, graph, node, parent=None):
        super().__init__(graph, parent)
        self.nodeDict = node.toDict()
        self.nodeName = node.getName()
        self.setText(f"Remove Node {self.nodeName}")
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
            self.graph._restoreOutEdges(self.outEdges, self.outListAttributes)


class DuplicateNodesCommand(GraphCommand):
    """
    Handle node duplication in a Graph.
    """
    def __init__(self, graph, srcNodes, parent=None):
        super().__init__(graph, parent)
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
    def __init__(self, graph: "Graph", data: dict, position: Position, parent=None):
        super().__init__(graph, parent)
        self.data = data
        self.position = position
        self.nodeNames: list[str] = []

    def redoImpl(self):
        graph = Graph("")
        try:
            graph._deserialize(self.data)
        except:
            return False

        boundingBoxCenter = self._boundingBoxCenter(graph.nodes)
        offset = Position(self.position.x - boundingBoxCenter.x, self.position.y - boundingBoxCenter.y)

        for node in graph.nodes:
            node.position = Position(node.position.x + offset.x, node.position.y + offset.y)

        nodes = self.graph.importGraphContent(graph)

        self.nodeNames = [node.name for node in nodes]
        self.setText(f"Paste Node{'s' if len(self.nodeNames) > 1 else ''} ({', '.join(self.nodeNames)})")
        return nodes

    def undoImpl(self):
        for name in self.nodeNames:
            self.graph.removeNode(name)

    def _boundingBox(self, nodes) -> tuple[int, int, int, int]:
        if not nodes:
            return (0, 0, 0 , 0)

        minX = maxX = nodes[0].x
        minY = maxY = nodes[0].y

        for node in nodes[1:]:
            minX = min(minX, node.x)
            minY = min(minY, node.y)
            maxX = max(maxX, node.x)
            maxY = max(maxY, node.y)

        return (minX, minY, maxX, maxY)

    def _boundingBoxCenter(self, nodes):
        minX, minY, maxX, maxY = self._boundingBox(nodes)
        return Position((minX + maxX) / 2, (minY + maxY) / 2)

class ImportProjectCommand(GraphCommand):
    """
    Handle the import of a project into a Graph.
    """

    def __init__(self, graph: Graph, filepath: PathLike, position=None, yOffset=0, parent=None):
        super().__init__(graph, parent)
        self.filepath = filepath
        self.importedNames = []
        self.position = position
        self.yOffset = yOffset

    def redoImpl(self):
        importedNodes = self.graph.importGraphContentFromFile(self.filepath)
        self.setText(f"Import Project ({len(importedNodes)} nodes)")

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
        super().__init__(graph, parent)
        self.attrName = attribute.fullName
        self.value = value
        self.oldValue = attribute.getSerializedValue()
        self.setText(f"Set Attribute '{attribute.fullName}'")

    def redoImpl(self):
        if self.value == self.oldValue:
            return False
        if self.graph.attribute(self.attrName) is not None:
            attribute = self.graph.attribute(self.attrName)
        else:
            attribute = self.graph.internalAttribute(self.attrName)

        attribute.value = self.value        

        return True

    def undoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            attribute = self.graph.attribute(self.attrName)
        else:
            attribute = self.graph.internalAttribute(self.attrName)

        attribute.value = self.oldValue

class AddAttributeKeyValueCommand(GraphCommand):
    def __init__(self, graph, attribute, key, value, parent=None):
        super().__init__(graph, parent)
        self.attrName = attribute.fullName
        self.keyable = attribute.keyable
        self.key = key
        self.value = value
        self.oldValue = None
        if attribute.keyable and attribute.keyValues.hasKey(key):
             self.oldValue = attribute.keyValues.pairs.get(int(key)).value
        self.setText(f"Add (key, value) for attribute '{attribute.fullName}' at key: '{key}'")

    def redoImpl(self):
        if not self.keyable or self.value == self.oldValue:
            return False
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).keyValues.add(self.key, self.value)
        else:
            self.graph.internalAttribute(self.attrName).keyValues.add(self.key, self.value)
        return True

    def undoImpl(self):
        if not self.keyable or self.value == self.oldValue:
            return False
        if self.graph.attribute(self.attrName) is not None:
            if self.oldValue is None:
                self.graph.attribute(self.attrName).keyValues.remove(self.key)
            else:
                self.graph.attribute(self.attrName).keyValues.add(self.key, self.oldValue)
        else:
            if self.oldValue is None:
                self.graph.internalAttribute(self.attrName).keyValues.remove(self.key)
            else:
                self.graph.internalAttribute(self.attrName).keyValues.add(self.key, self.oldValue)
        return True

class RemoveAttributeKeyCommand(GraphCommand):
    def __init__(self, graph, attribute, key, parent=None):
        super().__init__(graph, parent)
        self.attrName = attribute.fullName
        self.keyable = attribute.keyable
        self.key = key
        self.oldValue = None
        if attribute.keyable and attribute.keyValues.hasKey(key):
             self.oldValue = attribute.keyValues.pairs.get(int(key)).value
        self.setText(f"Remove (key, value) for attribute '{attribute.fullName}' at key: '{key}'")

    def redoImpl(self):
        if not self.keyable or self.oldValue == None:
            return False
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).keyValues.remove(self.key)
        else:
            self.graph.internalAttribute(self.attrName).keyValues.remove(self.key)
        return True

    def undoImpl(self):
        if not self.keyable or self.oldValue == None:
            return False
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).keyValues.add(self.key, self.oldValue)
        else:
            self.graph.internalAttribute(self.attrName).keyValues.add(self.key, self.oldValue)
        return True

class SetObservationCommand(GraphCommand):
    def __init__(self, graph, attribute, key, observation, parent=None):
        super().__init__(graph, parent)
        self.attrName = attribute.fullName
        self.key = key
        self.observation = observation.toVariant()
        self.oldObservation = attribute.geometry.getObservation(key)
        self.setText(f"Set observation for shape attribute '{attribute.fullName}' at key: '{key}'")

    def redoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).geometry.setObservation(self.key, self.observation)
        else:
            self.graph.internalAttribute(self.attrName).geometry.setObservation(self.key, self.observation)
        return True

    def undoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            if self.oldObservation is None:
                self.graph.attribute(self.attrName).geometry.removeObservation(self.key)
            else:
                self.graph.attribute(self.attrName).geometry.setObservation(self.key, self.oldObservation)
        else:
            if self.oldObservation is None:
                self.graph.internalAttribute(self.attrName).geometry.removeObservation(self.key)
            else:
                self.graph.internalAttribute(self.attrName).geometry.setObservation(self.key, self.oldObservation)
        return True

class RemoveObservationCommand(GraphCommand):
    def __init__(self, graph, attribute, key, parent=None):
        super().__init__(graph, parent)
        self.attrName = attribute.fullName
        self.key = key
        self.oldObservation = attribute.geometry.getObservation(key)
        self.setText(f"Remove observation for shape attribute '{attribute.fullName}' at key: '{key}'")

    def redoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).geometry.removeObservation(self.key)
        else:
            self.graph.internalAttribute(self.attrName).geometry.removeObservation(self.key)
        return True

    def undoImpl(self):
        if self.graph.attribute(self.attrName) is not None:
            self.graph.attribute(self.attrName).geometry.setObservation(self.key, self.oldObservation)
        else:
            self.graph.internalAttribute(self.attrName).geometry.setObservation(self.key, self.oldObservation)
        return True

class AddEdgeCommand(GraphCommand):
    def __init__(self, graph, src, dst, parent=None):
        super().__init__(graph, parent)
        self.srcAttr = src.fullName
        self.dstAttr = dst.fullName
        self.createdEdges = []  # List of all the edges that have been created at once
        self.deletedEdges = []  # List of all the edges that have been deleted to create the new edge(s)
        self.setText(f"Connect '{self.srcAttr}' -> '{self.dstAttr}'")

        if not dst.validateIncomingConnection(src):
            raise InvalidEdgeError(src.fullName, dst.fullName, "Attributes are not compatible.")

    def redoImpl(self) -> bool:
        try:
            self.createdEdges, self.deletedEdges = self.graph.attribute(self.srcAttr).connectTo(self.graph.attribute(self.dstAttr))
        except CyclicDependencyError:
            self.graph.removeEdge(self.graph.attribute(self.dstAttr))
            return False
        return True

    def undoImpl(self) -> bool:
        for edge in self.createdEdges:
            edge[1].disconnectEdge()
        for edge in self.deletedEdges:
            edge[0].connectTo(edge[1])
        return True


class RemoveEdgeCommand(GraphCommand):
    def __init__(self, graph, edge, parent=None):
        super().__init__(graph, parent)
        self.srcAttr = edge.src.fullName
        self.dstAttr = edge.dst.fullName
        self.deletedEdgeNames = []  # Store the names of deleted edges.
        self.setText(f"Disconnect '{self.srcAttr}' -> '{self.dstAttr}'")

    def redoImpl(self) -> bool:
        deletedEdges = self.graph.attribute(self.dstAttr).disconnectEdge()
        # Store the fullNames instead of the actual attribute objects
        self.deletedEdgeNames = [
            (edge[0].fullName, edge[1].fullName) for edge in deletedEdges
        ]
        return True

    def undoImpl(self) -> bool:
        for srcName, dstName in self.deletedEdgeNames:
            # Resolve the attributes from their names at undo time
            # This way for ListAttribute we avoid getting a deleted object
            srcAttr = self.graph.attribute(srcName)
            dstAttr = self.graph.attribute(dstName)
            srcAttr.connectTo(dstAttr)
        return True


class ListAttributeAppendCommand(GraphCommand):
    def __init__(self, graph, listAttribute, value, parent=None):
        super().__init__(graph, parent)
        assert isinstance(listAttribute, ListAttribute)
        self.attrName = listAttribute.fullName
        self.index = None
        self.count = 1
        self.value = value if value else None
        self.setText(f"Append to {self.attrName}")

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
        super().__init__(graph, parent)
        listAttribute = attribute.root
        assert isinstance(listAttribute, ListAttribute)
        self.listAttrName = listAttribute.fullName
        self.index = listAttribute.index(attribute)
        self.value = attribute.getSerializedValue()
        self.setText(f"Remove {attribute.fullName}")

    def redoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.remove(self.index)
        return True

    def undoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.insert(self.index, self.value)


class RemoveImagesCommand(GraphCommand):
    """
    Remove all the images from one or several CameraInit nodes as a single operation.
    Both the viewpoints and intrinsics lists are reset to their default values.
    """
    def __init__(self, graph, cameraInitNodes, parent=None):
        super().__init__(graph, parent)
        self.cameraInits = cameraInitNodes
        self.viewpoints = { cameraInit.name: cameraInit.attribute("viewpoints").getSerializedValue() for cameraInit in self.cameraInits }
        self.intrinsics = { cameraInit.name: cameraInit.attribute("intrinsics").getSerializedValue() for cameraInit in self.cameraInits }
        self.title = f"Remove{' ' if len(self.cameraInits) == 1 else ' All '}Images"
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


class RemoveSelectedImagesCommand(GraphCommand):
    """
    Remove a specific subset of images (viewpoints and their orphaned intrinsics) from a single
    CameraInit node as a single operation.
    """
    def __init__(self, graph, cameraInitNode, imagesToRemove, parent=None):
        super().__init__(graph, parent)
        self.cameraInitNode = cameraInitNode

        # Save current state of viewpoints and intrinsics
        self.oldViewpoints = cameraInitNode.attribute("viewpoints").getSerializedValue()
        self.oldIntrinsics = cameraInitNode.attribute("intrinsics").getSerializedValue()

        # Build a set of viewIds to remove based on the provided images list and then the new viewpoints list
        removeViewIds = {image.viewId.value for image in imagesToRemove}
        self.newViewpoints = [vp for vp in self.oldViewpoints if vp.get("viewId") not in removeViewIds]

        # Compute set of intrinsicIds that are still referenced by the remaining viewpoints and then
        # the new intrinsics list
        keptIntrinsicIds = {vp.get("intrinsicId") for vp in self.newViewpoints}
        self.newIntrinsics = [intr for intr in self.oldIntrinsics if intr.get("intrinsicId") in keptIntrinsicIds]

        self.title = f"Remove {len(removeViewIds)} Image{'(s)' if len(removeViewIds) > 1 else ''}"
        self.setText(self.title)

    def redoImpl(self):
        with GraphModification(self.graph):
            self.cameraInitNode.viewpoints.value = self.newViewpoints
            self.cameraInitNode.intrinsics.value = self.newIntrinsics
        return True

    def undoImpl(self):
        with GraphModification(self.graph):
            self.cameraInitNode.viewpoints.value = self.oldViewpoints
            self.cameraInitNode.intrinsics.value = self.oldIntrinsics


class MoveNodeCommand(GraphCommand):
    """ Move a node to a given position. """
    def __init__(self, graph, node, position, parent=None):
        super().__init__(graph, parent)
        self.nodeName = node.name
        self.oldPosition = node.position
        self.newPosition = position
        self.setText(f"Move {self.nodeName}")

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
        super().__init__(graph, parent)
        self.nodeDict = node.toDict()
        self.nodeName = node.getName()
        self.compatibilityIssue = None
        self.setText(f"Upgrade Node {self.nodeName}")

    def redoImpl(self):
        if not (node := self.graph.node(self.nodeName)).canUpgrade:
            return False
        self.compatibilityIssue = node.issue
        return self.graph.upgradeNode(self.nodeName)

    def undoImpl(self):
        expectedUid = None
        if self.compatibilityIssue == CompatibilityIssue.UidConflict:
            expectedUid = self.graph.node(self.nodeName)._uid

        # recreate compatibility node
        with GraphModification(self.graph):
            node = nodeFactory(self.nodeDict, name=self.nodeName, expectedUid=expectedUid)
            self.graph.replaceNode(self.nodeName, node)


class EnableGraphUpdateCommand(GraphCommand):
    """ Command to enable/disable graph update.
    Should not be used directly, use GroupedGraphModification context manager instead.
    """
    def __init__(self, graph, enabled, parent=None):
        super().__init__(graph, parent)
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
