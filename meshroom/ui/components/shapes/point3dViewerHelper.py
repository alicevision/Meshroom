from PySide6.QtGui import QVector3D

from meshroom.common import BaseObject, Property, Variant, Signal, Slot
from meshroom.core.point3d import getNodePoint3dPositions
from meshroom.core.point3d import getNodePoint3dPositions, getSelectedPoint3dObservationKey


class Point3dViewerHelper(BaseObject):
    """
    Exposes the selected node Point3d shapes as QVector3D positions for Viewer3D.
    """

    def __init__(self, activeProject, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._currentNode = None
        self._positions = []
        self._hasSelectedNodePoint3d = False
        self._connectedSignals = []

        self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)
        self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
        self._onSelectedNodeChanged()

    @classmethod
    def getPoint3dPositions(cls, node, viewId):
        return [QVector3D(x, y, z) for x, y, z in getNodePoint3dPositions(node, viewId)]

    def _getPositions(self):
        return self._positions

    def _getHasSelectedNodePoint3d(self):
        return self._hasSelectedNodePoint3d

    def _connectSignal(self, signal, callback):
        signal.connect(callback)
        self._connectedSignals.append((signal, callback))

    def _disconnectSignals(self):
        for signal, callback in self._connectedSignals:
            try:
                signal.disconnect(callback)
            except (RuntimeError, TypeError):
                pass
        self._connectedSignals = []

    def _connectPoint3dAttribute(self, shapeAttribute):
        self._connectSignal(shapeAttribute.geometryChanged, self._refreshPositions)
        self._connectSignal(shapeAttribute.shapeChanged, self._refreshPositions)

    def _rebuildAttributeConnections(self):
        self._disconnectSignals()

        if self._currentNode is None:
            return

        for attr in self._currentNode.attributes:
            if attr.type == "Point3d":
                self._connectPoint3dAttribute(attr)
                continue

            if attr.type == "ShapeList" and attr.desc.elementDesc.__class__.__name__ == "Point3d":
                self._connectSignal(attr.valueChanged, self._onShapeListChanged)
                self._connectSignal(attr.shapeListChanged, self._refreshPositions)
                for childAttr in attr.value:
                    if childAttr.type == "Point3d":
                        self._connectPoint3dAttribute(childAttr)

    @Slot()
    def _onShapeListChanged(self):
        self._rebuildAttributeConnections()
        self._refreshPositions()

    @Slot()
    def _onSelectedNodeChanged(self):
        self._currentNode = self._activeProject.selectedNode
        self._rebuildAttributeConnections()
        self._refreshPositions()

    @Slot()
    def _onSelectedViewIdChanged(self):
        self._refreshPositions()

    @Slot(str, result=str)
    def observationKeyForSelectedPoint3d(self, selectedShapeName):
        return getSelectedPoint3dObservationKey(
            self._activeProject.graph,
            self._currentNode,
            selectedShapeName,
            self._activeProject.selectedViewId,
        )

    @Slot()
    def _refreshPositions(self):
        node = self._currentNode
        positions = self.getPoint3dPositions(node, self._activeProject.selectedViewId) if node else []
        hasSelectedNodePoint3d = bool(positions)

        self._positions = positions
        self.positionsChanged.emit()

        if self._hasSelectedNodePoint3d != hasSelectedNodePoint3d:
            self._hasSelectedNodePoint3d = hasSelectedNodePoint3d
            self.hasSelectedNodePoint3dChanged.emit()

    positionsChanged = Signal()
    positions = Property(Variant, _getPositions, notify=positionsChanged)

    hasSelectedNodePoint3dChanged = Signal()
    hasSelectedNodePoint3d = Property(bool, _getHasSelectedNodePoint3d, notify=hasSelectedNodePoint3dChanged)