from PySide6.QtGui import QVector3D

from meshroom.common import BaseObject, Property, Variant, Signal, Slot
from .surveyPoint import (getNodeSurveyPointData, getSurveyPointObservationKey, mergeSurveyPointObservation,
                          resolveSelectedSurveyPointAttribute)


class SurveyPointViewerHelper(BaseObject):
    """
    Exposes the selected node SurveyPoint shapes as QVector3D positions for Viewer3D,
    along with the index of the selected SurveyPoint in these positions.
    """

    def __init__(self, activeProject, shapeViewerHelper, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._shapeViewerHelper = shapeViewerHelper
        self._currentNode = None
        self._positions = []
        self._positionNames = []  # Full name of the SurveyPoint at each index of positions
        self._selectedIndex = -1
        self._hasSelectedNodeSurveyPoint = False
        self._connectedSignals = []

        self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)
        self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
        self._shapeViewerHelper.selectedShapeNamesChanged.connect(self._refreshSelectedIndex)
        self._onSelectedNodeChanged()

    def _getPositions(self):
        return self._positions

    def _getSelectedIndex(self):
        return self._selectedIndex

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

    @Slot(str, float, float, float)
    def setPickedPosition(self, shapeName, x, y, z):
        """
        Set the 3d part of the given SurveyPoint for the selected view, keeping its 2d part.
        Does nothing if the shape is not a visible SurveyPoint of the selected node, or without selected view
        for a keyable SurveyPoint.

        Args:
            shapeName: the SurveyPoint full name.
            x, y, z: the picked position, in the SurveyPoint coordinates.
        """
        shape = resolveSelectedSurveyPointAttribute(self._activeProject.graph, self._currentNode, shapeName)
        key = getSurveyPointObservationKey(shape, self._activeProject.selectedViewId)
        if key is None:
            return
        observation = mergeSurveyPointObservation(shape, key, {"X": x, "Y": y, "Z": z, "picked3d": True})
        self._activeProject.setObservation(shape, key, observation)

    @Slot()
    def _refreshPositions(self):
        node = self._currentNode
        data = getNodeSurveyPointData(node, self._activeProject.selectedViewId) if node else []
        pickedData = [item for item in data if item["picked3d"]]
        hasSelectedNodeSurveyPoint = bool(pickedData)

        self._positions = [QVector3D(*item["position"]) for item in pickedData]
        self._positionNames = [item["fullName"] for item in pickedData]
        self.positionsChanged.emit()

        if self._hasSelectedNodeSurveyPoint != hasSelectedNodeSurveyPoint:
            self._hasSelectedNodeSurveyPoint = hasSelectedNodeSurveyPoint
            self.hasSelectedNodeSurveyPointChanged.emit()

        self._refreshSelectedIndex()

    @Slot()
    def _refreshSelectedIndex(self):
        """
        Set the index in positions of the single selected shape, or -1 if it has no position
        (nothing or several shapes selected, a ShapeList or a SurveyPoint without picked 3d position).
        """
        selectedShapeNames = self._shapeViewerHelper.selectedShapeNames
        selectedIndex = -1
        if len(selectedShapeNames) == 1 and selectedShapeNames[0] in self._positionNames:
            selectedIndex = self._positionNames.index(selectedShapeNames[0])

        if self._selectedIndex != selectedIndex:
            self._selectedIndex = selectedIndex
            self.selectedIndexChanged.emit()

    positionsChanged = Signal()
    positions = Property(Variant, _getPositions, notify=positionsChanged)

    selectedIndexChanged = Signal()
    selectedIndex = Property(int, _getSelectedIndex, notify=selectedIndexChanged)

    hasSelectedNodeSurveyPointChanged = Signal()
    hasSelectedNodeSurveyPoint = Property(bool, _getHasSelectedNodeSurveyPoint, notify=hasSelectedNodeSurveyPointChanged)
