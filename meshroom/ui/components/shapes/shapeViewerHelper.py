from meshroom.common import BaseObject, Property, Variant, Signal, Slot

class ShapeViewerHelper(BaseObject):
    """
    Manages interactions with the qml ShapeViewer (2d Viewer).
    - Handle shape selection.
    - Handle shape observation initialization.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selectedShapeName = ""
        self._containerWidth = 0.0
        self._containerHeight = 0.0
        self._containerScale = 0.0

    def _getSelectedShapeName(self) -> str:
        return self._selectedShapeName

    def _getContainerWidth(self) -> float:
        return self._containerWidth

    def _getContainerHeight(self) -> float:
        return self._containerHeight

    def _getContainerScale(self) -> float:
        return self._containerScale

    def _setSelectedShapeName(self, shapeName:str):
        self._selectedShapeName = shapeName
        self.selectedShapeNameChanged.emit()

    def _setContainerWidth(self, width: float):
        self._containerWidth = width
        self.containerWidthChanged.emit()

    def _setContainerHeight(self, height: float):
        self._containerHeight= height
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
                return { "x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5}
            case "Line2d":
                return { "a": { "x": self._containerWidth * 0.4, "y": self._containerHeight * 0.4},
                         "b": { "x": self._containerWidth * 0.6, "y": self._containerHeight * 0.6}}
            case "Circle":
                return { "center": {"x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5},
                         "radius": self._containerWidth * 0.1}
            case "Rectangle":
                return { "center": { "x": self._containerWidth * 0.5, "y": self._containerHeight * 0.5},
                         "size": { "width": self._containerWidth * 0.2, "height": self._containerHeight * 0.2}}
        return None

    # Properties and signals
    selectedShapeNameChanged = Signal()
    selectedShapeName = Property(str, _getSelectedShapeName, _setSelectedShapeName, notify=selectedShapeNameChanged)

    containerWidthChanged = Signal()
    containerWidth = Property(float, _getContainerWidth, _setContainerWidth, notify=containerWidthChanged)

    containerHeightChanged = Signal()
    containerHeight = Property(float, _getContainerHeight, _setContainerHeight, notify=containerHeightChanged)

    containerScaleChanged = Signal()
    containerScale = Property(float, _getContainerScale, _setContainerScale, notify=containerScaleChanged)
