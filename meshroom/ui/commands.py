from PySide2.QtWidgets import QUndoCommand, QUndoStack
from PySide2.QtCore import Property, Signal
from meshroom.core.graph import Node


class UndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        super(UndoCommand, self).__init__(parent)
        self._enabled = True

    def setEnabled(self, enabled):
        self._enabled = enabled

    def redo(self):
        if not self._enabled:
            return
        self.redoImpl()

    def undo(self):
        if not self._enabled:
            return
        self.undoImpl()

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
        if command.redoImpl():
            command.setEnabled(False)
            self.push(command)  # takes ownership
            command.setEnabled(True)
            return True
        else:
            return False

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
        self.node = None

    def redoImpl(self):
        self.node = self.graph.addNewNode(self.nodeType)
        self.setText("Add Node {}".format(self.node.getName()))
        self.node._applyExpr()
        return True

    def undoImpl(self):
        self.graph.removeNode(self.node.getName())
        self.node = None


class RemoveNodeCommand(GraphCommand):
    def __init__(self, graph, node, parent=None):
        super(RemoveNodeCommand, self).__init__(graph, parent)
        self.nodeDesc = node.toDict()
        self.nodeName = node.getName()
        self.setText("Remove Node {}".format(self.nodeName))
        self.edges = {}

    def redoImpl(self):
        self.edges = self.graph.removeNode(self.nodeName)
        return True

    def undoImpl(self):
        node = self.graph.addNode(Node(nodeDesc=self.nodeDesc["nodeType"],
                                       parent=self.graph, **self.nodeDesc["attributes"]
                                       ), self.nodeName)
        assert (node.getName() == self.nodeName)

        # recreate edges deleted on node removal
        for key, value in self.edges.items():
            iNode, iAttr = key.split(".")
            oNode, oAttr = value.split(".")
            self.graph.addEdge(self.graph.node(oNode).attribute(oAttr),
                               self.graph.node(iNode).attribute(iAttr))

        node.updateInternals()


class SetAttributeCommand(GraphCommand):
    def __init__(self, graph, attribute, value, parent=None):
        super(SetAttributeCommand, self).__init__(graph, parent)
        self.nodeName = attribute.node.getName()
        self.attrName = attribute.getName()
        self.value = value
        self.oldValue = attribute.value
        self.setText("Set Attribute '{}'".format(attribute.fullName()))

    def redoImpl(self):
        if self.value == self.oldValue:
            return False
        self.graph.node(self.nodeName).attribute(self.attrName).value = self.value
        return True

    def undoImpl(self):
        self.graph.node(self.nodeName).attribute(self.attrName).value = self.oldValue


class AddEdgeCommand(GraphCommand):
    def __init__(self, graph, src, dst, parent=None):
        super(AddEdgeCommand, self).__init__(graph, parent)
        self.srcNode, self.srcAttr = src.fullName().split(".")
        self.dstNode, self.dstAttr = dst.fullName().split(".")
        self.setText("Connect '{}'->'{}'".format(src.fullName(), dst.fullName()))

    def redoImpl(self):
        try:
            self.graph.addEdge(self.graph.node(self.srcNode).attribute(self.srcAttr),
                               self.graph.node(self.dstNode).attribute(self.dstAttr))
        except RuntimeError:
            return False
        return True

    def undoImpl(self):
        self.graph.removeEdge(self.graph.node(self.dstNode).attribute(self.dstAttr))


class RemoveEdgeCommand(GraphCommand):
    def __init__(self, graph, edge, parent=None):
        super(RemoveEdgeCommand, self).__init__(graph, parent)
        self.srcNode, self.srcAttr = edge.src.fullName().split(".")
        self.dstNode, self.dstAttr = edge.dst.fullName().split(".")
        self.setText("Disconnect '{}'->'{}'".format(edge.src.fullName(), edge.dst.fullName()))

    def redoImpl(self):
        self.graph.removeEdge(self.graph.node(self.dstNode).attribute(self.dstAttr))
        return True

    def undoImpl(self):
        self.graph.addEdge(self.graph.node(self.srcNode).attribute(self.srcAttr),
                           self.graph.node(self.dstNode).attribute(self.dstAttr))
