from PySide6.QtCore import QObject

from meshroom.common import BaseObject, Property, Variant, Signal, Slot


class ShapeViewerHelper(BaseObject):
    """
    Manages interactions with the qml ShapeViewer (2d Viewer).
    - Handle shape selection.
    - Handle shape observation initialization.
    - Handle shape placement (click-to-place observation in the 2d Viewer).
    """

    def __init__(self, activeProject, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._selectedShapeName = ""
        self._selectedShape = None  # ShapeAttribute | ShapeListAttribute | None
        self._listPlacement = False  # ShapeList multi-add mode
        self._containerWidth = 0.0
        self._containerHeight = 0.0
        self._containerScale = 0.0
        self._activeProject.selectedViewIdChanged.connect(self.placementChanged)
        self._activeProject.selectedNodeChanged.connect(self.cancelPlacement)

    def _getSelectedShapeName(self) -> str:
        return self._selectedShapeName

    def _getContainerWidth(self) -> float:
        return self._containerWidth

    def _getContainerHeight(self) -> float:
        return self._containerHeight

    def _getContainerScale(self) -> float:
        return self._containerScale

    def _setSelectedShapeName(self, shapeName: str):
        """
        Set the selected shape name.
        Selecting another shape (or none) cancels the current placement.
        """
        if self._selectedShape is not None and shapeName != self._selectedShape.fullName:
            self._setSelectedShape(None)
            self._listPlacement = False
        self._selectedShapeName = shapeName
        self.selectedShapeNameChanged.emit()
        self.placementChanged.emit()

    def _setSelectedShape(self, shape):
        """
        Set the selected shape object and track its observations to update the placement state.

        Args:
            shape: the ShapeAttribute or ShapeListAttribute to track, or None.
        """
        if self._selectedShape is not None and self._selectedShape.type != "ShapeList":
            try:
                self._selectedShape.geometry.observationsChanged.disconnect(self.placementChanged)
            except RuntimeError:
                # Signal was already disconnected or the attribute was destroyed
                pass
        self._selectedShape = shape
        if shape is not None and shape.type != "ShapeList":
            shape.geometry.observationsChanged.connect(self.placementChanged)
        self.placementChanged.emit()

    def _hasCurrentObservation(self, shape) -> bool:
        """Whether the given shape has an observation for the current view."""
        geometry = shape.geometry
        if geometry.observationKeyable:
            return geometry.hasObservation(self._activeProject.selectedViewId)
        return not geometry.isDefault

    def _isPlacing(self) -> bool:
        """Whether the 2d Viewer is waiting for a click to place the selected shape."""
        if self._selectedShape is None:
            return False
        if self._selectedShape.type == "ShapeList":
            return self._listPlacement
        return not self._hasCurrentObservation(self._selectedShape)

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
        self.selectedShapeName = shape.fullName

    @Slot(QObject)
    def startListPlacement(self, listAttribute):
        """Select the given ShapeList and start the multi-add placement mode."""
        self.selectShape(listAttribute)
        self._listPlacement = True
        self.placementChanged.emit()

    @Slot()
    def cancelPlacement(self):
        """Cancel the current placement and clear the selection."""
        self.selectedShapeName = ""

    @Slot(str, float, float, float, float, result=Variant)
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

    @Slot(float, float, float, float)
    def placeSelectedShapeAt(self, x: float, y: float, visibleWidth: float, visibleHeight: float):
        """
        Set the selected shape observation for the current view at the given image position.
        For a ShapeList, append a new element with its observation (single undo step).
        """
        shape = self._selectedShape
        if shape is None:
            return
        viewId = self._activeProject.selectedViewId
        if shape.type == "ShapeList":
            with self._activeProject.groupedGraphModification("Add Shape"):
                self._activeProject.appendAttribute(shape, None)
                element = shape.at(len(shape) - 1)
                self._activeProject.setObservation(element, viewId,
                                                   self.getObservationAt(element.type, x, y, visibleWidth, visibleHeight))
        else:
            self._activeProject.setObservation(shape, viewId,
                                               self.getObservationAt(shape.type, x, y, visibleWidth, visibleHeight))

    # Properties and signals
    selectedShapeNameChanged = Signal()
    selectedShapeName = Property(str, _getSelectedShapeName, _setSelectedShapeName, notify=selectedShapeNameChanged)

    containerWidthChanged = Signal()
    containerWidth = Property(float, _getContainerWidth, _setContainerWidth, notify=containerWidthChanged)

    containerHeightChanged = Signal()
    containerHeight = Property(float, _getContainerHeight, _setContainerHeight, notify=containerHeightChanged)

    containerScaleChanged = Signal()
    containerScale = Property(float, _getContainerScale, _setContainerScale, notify=containerScaleChanged)

    placementChanged = Signal()
    selectedShape = Property(Variant, lambda self: self._selectedShape, notify=placementChanged)
    isListPlacement = Property(bool, lambda self: self._listPlacement, notify=placementChanged)
    isPlacing = Property(bool, _isPlacing, notify=placementChanged)
