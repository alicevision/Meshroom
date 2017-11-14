import logging
import traceback
from PySide2.QtWidgets import QUndoCommand, QUndoStack
from PySide2.QtCore import Property, Signal
from meshroom.core.graph import Node, ListAttribute


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

    def tryAndPush(self, command):
        # type: (UndoCommand) -> bool
        try:
            res = command.redoImpl()
        except Exception as e:
            logging.error("Error while trying command '{}': \n{}".format(command.text(), traceback.format_exc()))
            res = False
        if res:
            command.setEnabled(False)
            self.push(command)  # takes ownership
            command.setEnabled(True)
        return res

    # Redeclare QUndoStack signal since original ones can not be used for properties notifying
    _cleanChanged = Signal()
    _canUndoChanged = Signal()
    _canRedoChanged = Signal()
    _undoTextChanged = Signal()
    _redoTextChanged = Signal()

    clean = Property(bool, QUndoStack.isClean, notify=_cleanChanged)
    canUndo = Property(bool, QUndoStack.canUndo, notify=_canRedoChanged)
    canRedo = Property(bool, QUndoStack.canRedo, notify=_canUndoChanged)
    undoText = Property(str, QUndoStack.undoText, notify=_undoTextChanged)
    redoText = Property(str, QUndoStack.redoText, notify=_redoTextChanged)


class GraphCommand(UndoCommand):
    def __init__(self, graph, parent=None):
        super(GraphCommand, self).__init__(parent)
        self.graph = graph


class AddNodeCommand(GraphCommand):
    def __init__(self, graph, nodeType, parent=None):
        super(AddNodeCommand, self).__init__(graph, parent)
        self.nodeType = nodeType
        self.nodeName = None

    def redoImpl(self):
        self.nodeName = self.graph.addNewNode(self.nodeType).name
        self.setText("Add Node {}".format(self.nodeName))
        return True

    def undoImpl(self):
        self.graph.removeNode(self.nodeName)


class RemoveNodeCommand(GraphCommand):
    def __init__(self, graph, node, parent=None):
        super(RemoveNodeCommand, self).__init__(graph, parent)
        self.nodeDict = node.toDict()
        self.nodeName = node.getName()
        self.setText("Remove Node {}".format(self.nodeName))
        self.outEdges = {}

    def redoImpl(self):
        # only keep outEdges since inEdges are serialized in nodeDict
        inEdges, self.outEdges = self.graph.removeNode(self.nodeName)
        return True

    def undoImpl(self):
        node = self.graph.addNode(Node(nodeDesc=self.nodeDict["nodeType"],
                                       **self.nodeDict["attributes"]
                                       ), self.nodeName)
        assert (node.getName() == self.nodeName)
        # recreate out edges deleted on node removal
        for dstAttr, srcAttr in self.outEdges.items():
            self.graph.addEdge(self.graph.attribute(srcAttr),
                               self.graph.attribute(dstAttr))


class SetAttributeCommand(GraphCommand):
    def __init__(self, graph, attribute, value, parent=None):
        super(SetAttributeCommand, self).__init__(graph, parent)
        self.attrName = attribute.fullName()
        self.value = value
        self.oldValue = attribute.getPrimitiveValue(exportDefault=True)
        self.setText("Set Attribute '{}'".format(attribute.fullName()))

    def redoImpl(self):
        if self.value == self.oldValue:
            return False
        self.graph.attribute(self.attrName).value = self.value
        return True

    def undoImpl(self):
        self.graph.attribute(self.attrName).value = self.oldValue


class AddEdgeCommand(GraphCommand):
    def __init__(self, graph, src, dst, parent=None):
        super(AddEdgeCommand, self).__init__(graph, parent)
        self.srcAttr = src.fullName()
        self.dstAttr = dst.fullName()
        self.setText("Connect '{}'->'{}'".format(self.srcAttr, self.dstAttr))

    def redoImpl(self):
        self.graph.addEdge(self.graph.attribute(self.srcAttr), self.graph.attribute(self.dstAttr))
        return True

    def undoImpl(self):
        self.graph.removeEdge(self.graph.attribute(self.dstAttr))


class RemoveEdgeCommand(GraphCommand):
    def __init__(self, graph, edge, parent=None):
        super(RemoveEdgeCommand, self).__init__(graph, parent)
        self.srcAttr = edge.src.fullName()
        self.dstAttr = edge.dst.fullName()
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
        self.attrName = listAttribute.fullName()
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
        self.listAttrName = listAttribute.fullName()
        self.index = listAttribute.index(attribute)
        self.value = attribute.getExportValue()
        self.setText("Remove {}".format(attribute.fullName()))

    def redoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.remove(self.index)
        return True

    def undoImpl(self):
        listAttribute = self.graph.attribute(self.listAttrName)
        listAttribute.insert(self.index, self.value)


