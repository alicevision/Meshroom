from PySide6.QtGui import QVector3D

from meshroom.common import BaseObject, Property, Variant, Signal, Slot
from meshroom.core.surveyPoint import getNodeSurveyPointPositions
from meshroom.core.surveyPoint import getNodeSurveyPointPositions, getSelectedSurveyPointObservationKey


class SurveyPointViewerHelper(BaseObject):
    """
    Exposes the selected node SurveyPoint shapes as QVector3D positions for Viewer3D.
    """

    def __init__(self, activeProject, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._currentNode = None
        self._positions = []
        self._hasSelectedNodeSurveyPoint = False
        self._connectedSignals = []

        self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)
        self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
        self._onSelectedNodeChanged()

    @classmethod
    def getSurveyPointPositions(cls, node, viewId):
        return [QVector3D(x, y, z) for x, y, z in getNodeSurveyPointPositions(node, viewId)]

    def _getPositions(self):
        return self._positions

    def _getHasSelectedNodeSurveyPoint(self):
        return self._hasSelectedNodeSurveyPoint

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

    def _connectSurveyPointAttribute(self, shapeAttribute):
        self._connectSignal(shapeAttribute.geometryChanged, self._refreshPositions)
        self._connectSignal(shapeAttribute.shapeChanged, self._refreshPositions)

    def _rebuildAttributeConnections(self):
        self._disconnectSignals()

        if self._currentNode is None:
            return

        for attr in self._currentNode.attributes:
            if attr.type == "SurveyPoint":
                self._connectSurveyPointAttribute(attr)
                continue

            if attr.type == "ShapeList" and attr.desc.elementDesc.__class__.__name__ == "SurveyPoint":
                self._connectSignal(attr.valueChanged, self._onShapeListChanged)
                self._connectSignal(attr.shapeListChanged, self._refreshPositions)
                for childAttr in attr.value:
                    if childAttr.type == "SurveyPoint":
                        self._connectSurveyPointAttribute(childAttr)

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
    def observationKeyForSelectedSurveyPoint(self, selectedShapeName):
        return getSelectedSurveyPointObservationKey(
            self._activeProject.graph,
            self._currentNode,
            selectedShapeName,
            self._activeProject.selectedViewId,
        )

    @Slot()
    def _refreshPositions(self):
        node = self._currentNode
        positions = self.getSurveyPointPositions(node, self._activeProject.selectedViewId) if node else []
        hasSelectedNodeSurveyPoint = bool(positions)

        self._positions = positions
        self.positionsChanged.emit()

        if self._hasSelectedNodeSurveyPoint != hasSelectedNodeSurveyPoint:
            self._hasSelectedNodeSurveyPoint = hasSelectedNodeSurveyPoint
            self.hasSelectedNodeSurveyPointChanged.emit()

    positionsChanged = Signal()
    positions = Property(Variant, _getPositions, notify=positionsChanged)

    hasSelectedNodeSurveyPointChanged = Signal()
    hasSelectedNodeSurveyPoint = Property(bool, _getHasSelectedNodeSurveyPoint, notify=hasSelectedNodeSurveyPointChanged)