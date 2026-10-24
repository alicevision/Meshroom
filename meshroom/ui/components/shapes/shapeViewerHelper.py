from PySide6.QtCore import QObject
from shiboken6 import isValid

from meshroom.common import BaseObject, Property, Variant, Signal, Slot
from meshroom.core.attribute import ListAttribute, ShapeListAttribute


class ShapeViewerHelper(BaseObject):
    """
    Manages interactions with the qml ShapeViewer (2d Viewer).
    - Handle shape selection (a list of shape names, ready for multiple selection).
    - Handle shape observation initialization.
    - Handle shape placement (click-to-place observation in the 2d Viewer).
    """

    def __init__(self, activeProject, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._selectedShapeNames = []  # Selected shape full names
        self._selectedShape = None  # ShapeAttribute | ShapeListAttribute | None
        self._listPlacement = False  # ShapeList multi-add mode
        self._containerWidth = 0.0
        self._containerHeight = 0.0
        self._containerScale = 0.0
        self._activeProject.selectedViewIdChanged.connect(self.placementChanged)
        self._activeProject.selectedNodeChanged.connect(self.cancelPlacement)

    def _getSelectedShapeNames(self) -> list:
        return self._selectedShapeNames

    def _getContainerWidth(self) -> float:
        return self._containerWidth

    def _getContainerHeight(self) -> float:
        return self._containerHeight

    def _getContainerScale(self) -> float:
        return self._containerScale

    def _setSelectedShapeNames(self, shapeNames: list):
        """
        Set the selected shape names.
        Selecting anything else than the placed shape alone cancels the current placement.
        """
        shapeNames = list(shapeNames)
        if self._selectedShape is not None and (not self._isSelectedShapeAlive()
                                                or shapeNames != [self._selectedShape.fullName]):
            self._setSelectedShape(None)
        self._selectedShapeNames = shapeNames
        self.selectedShapeNamesChanged.emit()
        self.placementChanged.emit()

    def _setSelectedShape(self, shape):
        """
        Set the selected shape object and track its observations to update the placement state.

        Args:
            shape: the ShapeAttribute or ShapeListAttribute to track, or None.
        """
        previousShape = self._selectedShape
        # Note: connections of a destroyed attribute are already gone
        if previousShape is not None and isValid(previousShape):
            try:
                if not isinstance(previousShape, ShapeListAttribute):
                    previousShape.geometry.observationsChanged.disconnect(self.placementChanged)
                if isinstance(previousShape.root, ListAttribute):
                    previousShape.root.valueChanged.disconnect(self._onSelectedShapeParentChanged)
            except RuntimeError:
                # Signal was already disconnected or the attribute was destroyed
                pass
        if shape is not previousShape:
            # A newly selected shape never starts in multi-add mode
            self._listPlacement = False
        self._selectedShape = shape
        if shape is not None:
            if not isinstance(shape, ShapeListAttribute):
                shape.geometry.observationsChanged.connect(self.placementChanged)
            # List element: cancel the selection if it is removed from its list
            if isinstance(shape.root, ListAttribute):
                shape.root.valueChanged.connect(self._onSelectedShapeParentChanged)
        self.placementChanged.emit()

    def _isSelectedShapeAlive(self) -> bool:
        """Whether the selected shape still exists and, for a list element, still belongs to its list."""
        shape = self._selectedShape
        if shape is None or not isValid(shape):
            return False
        parent = shape.root
        if isinstance(parent, ListAttribute):
            return isValid(parent) and any(element is shape for element in parent.value)
        return True

    def _onSelectedShapeParentChanged(self):
        """
        Callback when the selected list element parent list changes.
        Cancel the selection if the element was removed, otherwise follow its new index.
        """
        if not self._isSelectedShapeAlive():
            self.cancelPlacement()
        elif self._selectedShapeNames != [self._selectedShape.fullName]:
            self._selectedShapeNames = [self._selectedShape.fullName]
            self.selectedShapeNamesChanged.emit()

    def _hasCurrentObservation(self, shape) -> bool:
        """Whether the given shape has an observation for the current view."""
        geometry = shape.geometry
        if geometry.observationKeyable:
            return geometry.hasObservation(self._activeProject.selectedViewId)
        return not geometry.isDefault

    def _isShapeListSelected(self) -> bool:
        return self._isSelectedShapeAlive() and isinstance(self._selectedShape, ShapeListAttribute)

    def _setListPlacement(self, enabled: bool):
        """Enable or disable the multi-add placement mode, only available when a ShapeList is selected."""
        enabled = enabled and self._isShapeListSelected()
        if enabled == self._listPlacement:
            return
        self._listPlacement = enabled
        self.placementChanged.emit()

    def _isPlacing(self) -> bool:
        """Whether the 2d Viewer is waiting for a click to place the selected shape."""
        if not self._isSelectedShapeAlive():
            return False
        if isinstance(self._selectedShape, ShapeListAttribute):
            return self._listPlacement
        return not self._hasCurrentObservation(self._selectedShape)

    def _getPlacementShapeType(self) -> str:
        """The type of the shape to place (the element type for a ShapeList), or an empty string if not placing."""
        if not self._isPlacing():
            return ""
        shape = self._selectedShape
        return shape.desc.elementDesc.type if isinstance(shape, ShapeListAttribute) else shape.type

    def _setContainerWidth(self, width: float):
        self._containerWidth = width
        self.containerWidthChanged.emit()

    def _setContainerHeight(self, height: float):
        self._containerHeight = height
        self.containerHeightChanged.emit()

    def _setContainerScale(self, scale: float):
        self._containerScale = scale
        self.containerScaleChanged.emit()

    @Slot(str, result=Variant)
    def getDefaultObservation(self, shapeType: str) -> Variant:
        """
        Helper function to create a shape default observation.
        """
        match shapeType:
            case "Point2d":
                return {"x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5}
            case "Line2d":
                return {"a": {"x": self._containerWidth * 0.4, "y": self._containerHeight * 0.4},
                        "b": {"x": self._containerWidth * 0.6, "y": self._containerHeight * 0.6}}
            case "Circle":
                return {"center": {"x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5},
                        "radius": self._containerWidth * 0.1}
            case "Rectangle":
                return {"center": {"x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5},
                        "size": {"width": self._containerWidth * 0.2, "height": self._containerHeight * 0.2}}
        return None

    @Slot(QObject)
    def selectShape(self, shape):
        """
        Select the given shape.
        Placement starts if the shape has no observation for the current view.
        """
        self._setSelectedShape(shape)
        self.selectedShapeNames = [shape.fullName]

    @Slot(QObject)
    def startListPlacement(self, listAttribute):
        """Select the given ShapeList and start the multi-add placement mode."""
        self.selectShape(listAttribute)
        self._setListPlacement(True)

    @Slot()
    def clearSelection(self):
        """Clear the selection, which also cancels the current placement."""
        self.selectedShapeNames = []

    @Slot()
    def cancelPlacement(self):
        """Cancel the current placement and clear the selection."""
        self.clearSelection()

    def getObservationAt(self, shapeType: str, x: float, y: float, visibleWidth: float, visibleHeight: float) -> Variant:
        """
        Create a shape observation at the given image position, sized relative to the visible viewport.

        Args:
            shapeType: the shape type (Point2d, Line2d, Circle, Rectangle).
            x, y: the position in image coordinates.
            visibleWidth, visibleHeight: the visible viewport size in image coordinates.

        Returns:
            The observation dict, or None for an unknown shape type.
        """
        match shapeType:
            case "Point2d":
                return {"x": x, "y": y}
            case "Line2d":
                halfLength = visibleWidth / 6.0
                return {"a": {"x": x - halfLength, "y": y},
                        "b": {"x": x + halfLength, "y": y}}
            case "Circle":
                return {"center": {"x": x, "y": y},
                        "radius": min(visibleWidth, visibleHeight) / 6.0}
            case "Rectangle":
                return {"center": {"x": x, "y": y},
                        "size": {"width": visibleWidth / 3.0, "height": visibleHeight / 3.0}}
        return None

    def _placeSelectedShape(self, observation: dict):
        """
        Set the given observation to the selected shape for the current view.
        For a ShapeList, append a new element with this observation (single undo step).
        """
        if observation is None or not self._isSelectedShapeAlive():
            return
        shape = self._selectedShape
        viewId = self._activeProject.selectedViewId
        if isinstance(shape, ShapeListAttribute):
            with self._activeProject.groupedGraphModification("Add Shape"):
                self._activeProject.appendAttribute(shape, None)
                self._activeProject.setObservation(shape.at(len(shape) - 1), viewId, observation)
        else:
            self._activeProject.setObservation(shape, viewId, observation)

    @Slot(float, float, float, float)
    def placeSelectedShapeAt(self, x: float, y: float, visibleWidth: float, visibleHeight: float):
        """Place the selected shape at the given image position, sized relative to the visible viewport."""
        shapeType = self._getPlacementShapeType()
        if not shapeType:
            return
        self._placeSelectedShape(self.getObservationAt(shapeType, x, y, visibleWidth, visibleHeight))

    # Properties and signals
    selectedShapeNamesChanged = Signal()
    selectedShapeNames = Property("QVariantList", _getSelectedShapeNames, _setSelectedShapeNames,
                                  notify=selectedShapeNamesChanged)

    containerWidthChanged = Signal()
    containerWidth = Property(float, _getContainerWidth, _setContainerWidth, notify=containerWidthChanged)

    containerHeightChanged = Signal()
    containerHeight = Property(float, _getContainerHeight, _setContainerHeight, notify=containerHeightChanged)

    containerScaleChanged = Signal()
    containerScale = Property(float, _getContainerScale, _setContainerScale, notify=containerScaleChanged)

    placementChanged = Signal()
    isShapeListSelected = Property(bool, _isShapeListSelected, notify=placementChanged)
    isListPlacement = Property(bool, lambda self: self._listPlacement, _setListPlacement, notify=placementChanged)
    isPlacing = Property(bool, _isPlacing, notify=placementChanged)
