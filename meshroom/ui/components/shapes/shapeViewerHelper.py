import math

from PySide6.QtCore import QObject, QPointF
from shiboken6 import isValid

from meshroom.common import BaseObject, Property, Variant, Signal, Slot
from meshroom.core.attribute import ListAttribute, ShapeListAttribute


class ShapeViewerHelper(BaseObject):
    """
    Manages interactions with the qml ShapeViewer (2d Viewer).
    - Handle shape selection (a list of shape names, ready for multiple selection).
    - Handle shape observation initialization.
    - Handle shape placement (click-to-place, drag-to-define or click-to-move observation in the 2d Viewer).
    - Handle the move of a multiple selection (shared drag offset, then a single translation).
    """

    def __init__(self, activeProject, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._selectedShapeNames = []  # Selected shape full names
        self._selectedShape = None  # ShapeAttribute | ShapeListAttribute | None
        self._listPlacement = False  # ShapeList multi-add mode
        self._repositioning = False  # Move the selected shape observation on next click
        self._containerWidth = 0.0
        self._containerHeight = 0.0
        self._containerScale = 0.0
        self._selectionMoveSource = ""  # Name of the selected shape dragged to move the whole selection
        self._selectionMoveOffset = QPointF()
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
            # A newly selected shape never starts in multi-add or move mode
            self._listPlacement = False
            self._repositioning = False
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

    def _isShapeEditable(self, shape) -> bool:
        """Whether the given shape (not a ShapeList) can be edited and has an observation for the current view."""
        isLinked = shape.isLink or (isinstance(shape.root, ListAttribute) and shape.root.isLink)
        return shape.enabled and not isLinked and self._hasCurrentObservation(shape)

    def _getDisplayedShapes(self) -> list:
        """
        Return the editable shapes of the selected node displayed in the 2d Viewer for the current view,
        including the elements of its ShapeLists.
        """
        node = self._activeProject.selectedNode
        if node is None:
            return []
        shapes = []
        for attribute in node.attributes:
            if not attribute.hasDisplayableShape or not attribute.isVisible:
                continue
            elements = attribute.value if isinstance(attribute, ShapeListAttribute) else [attribute]
            shapes.extend(shape for shape in elements if shape.isVisible and self._isShapeEditable(shape))
        return shapes

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
        return self._repositioning or not self._hasCurrentObservation(self._selectedShape)

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

    @Slot(QObject)
    def startReposition(self, shape):
        """Select the given shape and move its observation for the current view on next click."""
        self.selectShape(shape)
        self._repositioning = True
        self.placementChanged.emit()

    @Slot(str)
    def toggleShapeSelection(self, shapeName: str):
        """Add the given shape name to the selection, or remove it if already selected."""
        if shapeName in self._selectedShapeNames:
            self.selectedShapeNames = [name for name in self._selectedShapeNames if name != shapeName]
        else:
            self.selectedShapeNames = self._selectedShapeNames + [shapeName]

    @Slot()
    def clearSelection(self):
        """Clear the selection, which also cancels the current placement."""
        self.selectedShapeNames = []

    @Slot()
    def cancelPlacement(self):
        """Cancel the current placement and clear the selection."""
        self.clearSelection()

    @Slot()
    def removeSelectedShapeObservation(self):
        """
        Remove the observation for the current view of all selected shapes (the shape itself if static,
        its current keyframe if keyable) in a single undo step, and clear the selection.
        ShapeLists, non-editable shapes and shapes without current observation are skipped.
        """
        graph = self._activeProject.graph
        if graph is None:
            return
        # Note: a shape selected from the 2d Viewer is only known by its name
        shapes = []
        for shapeName in self._selectedShapeNames:
            shape = graph.anyAttribute(shapeName)
            if shape is not None and not isinstance(shape, ShapeListAttribute) and self._isShapeEditable(shape):
                shapes.append(shape)
        if not shapes:
            return
        viewId = self._activeProject.selectedViewId
        with self._activeProject.groupedGraphModification("Remove Shape Observations"):
            for shape in shapes:
                self._activeProject.removeObservation(shape, viewId)
        self.cancelPlacement()

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

    @staticmethod
    def getDragObservation(shapeType: str, x0: float, y0: float, x1: float, y1: float) -> Variant:
        """
        Create a shape observation defined by a drag from (x0, y0) to (x1, y1).
        - Point2d: at the end position.
        - Line2d: from the start to the end position.
        - Circle: the largest circle inside the dragged rectangle, in the corner of the start position.
        - Rectangle: the dragged rectangle.

        Args:
            shapeType: the shape type (Point2d, Line2d, Circle, Rectangle).
            x0, y0: the drag start position in image coordinates.
            x1, y1: the drag end position in image coordinates.

        Returns:
            The observation dict, or None for an unknown shape type or an empty circle/rectangle.
        """
        dx, dy = x1 - x0, y1 - y0
        match shapeType:
            case "Point2d":
                return {"x": x1, "y": y1}
            case "Line2d":
                return {"a": {"x": x0, "y": y0}, "b": {"x": x1, "y": y1}}
            case "Circle":
                radius = min(abs(dx), abs(dy)) * 0.5
                if radius <= 0:
                    return None
                return {"center": {"x": x0 + math.copysign(radius, dx), "y": y0 + math.copysign(radius, dy)},
                        "radius": radius}
            case "Rectangle":
                if dx == 0 or dy == 0:
                    return None
                return {"center": {"x": (x0 + x1) * 0.5, "y": (y0 + y1) * 0.5},
                        "size": {"width": abs(dx), "height": abs(dy)}}
        return None

    @staticmethod
    def getMovedObservation(shapeType: str, observation: dict, x: float, y: float) -> dict:
        """
        Translate a shape observation so that its center lands on the given image position.

        Args:
            shapeType: the shape type (Point2d, Line2d, Circle, Rectangle).
            observation: the current observation, kept unchanged.
            x, y: the new center position in image coordinates.

        Returns:
            The moved observation dict, or None for an unknown shape type.
        """
        match shapeType:
            case "Point2d":
                return {"x": x, "y": y}
            case "Line2d":
                a, b = observation["a"], observation["b"]
                dx = x - (a["x"] + b["x"]) * 0.5
                dy = y - (a["y"] + b["y"]) * 0.5
                return {"a": {"x": a["x"] + dx, "y": a["y"] + dy},
                        "b": {"x": b["x"] + dx, "y": b["y"] + dy}}
            case "Circle" | "Rectangle":
                return {**observation, "center": {"x": x, "y": y}}
        return None

    @staticmethod
    def getTranslatedObservation(shapeType: str, observation: dict, dx: float, dy: float) -> dict:
        """
        Translate a shape observation by the given offset.

        Args:
            shapeType: the shape type (Point2d, Line2d, Circle, Rectangle).
            observation: the current observation, kept unchanged.
            dx, dy: the offset in image coordinates.

        Returns:
            The translated observation dict, or None for an unknown shape type.
        """
        match shapeType:
            case "Point2d":
                return {"x": observation["x"] + dx, "y": observation["y"] + dy}
            case "Line2d":
                a, b = observation["a"], observation["b"]
                return {"a": {"x": a["x"] + dx, "y": a["y"] + dy},
                        "b": {"x": b["x"] + dx, "y": b["y"] + dy}}
            case "Circle" | "Rectangle":
                center = observation["center"]
                return {**observation, "center": {"x": center["x"] + dx, "y": center["y"] + dy}}
        return None

    @Slot(str, float, float)
    def setSelectionMoveOffset(self, shapeName: str, dx: float, dy: float):
        """
        Share the drag offset of the given selected shape, so that the other selected shapes follow it.
        A null offset ends the selection move.
        """
        self._selectionMoveSource = shapeName if (dx or dy) else ""
        self._selectionMoveOffset = QPointF(dx, dy)
        self.selectionMoveChanged.emit()

    @Slot(float, float)
    def moveSelectedShapes(self, dx: float, dy: float):
        """
        Translate the current view observation of all the editable selected shapes by the given offset
        (single undo step), and end the selection move.
        """
        graph = self._activeProject.graph
        viewId = self._activeProject.selectedViewId
        if graph is not None and (dx or dy):
            with self._activeProject.groupedGraphModification("Move Shapes"):
                for shapeName in self._selectedShapeNames:
                    shape = graph.anyAttribute(shapeName)
                    if shape is None or isinstance(shape, ShapeListAttribute) or not self._isShapeEditable(shape):
                        continue
                    observation = self.getTranslatedObservation(shape.type, shape.geometry.getObservation(viewId), dx, dy)
                    if observation is not None:
                        self._activeProject.setObservation(shape, viewId, observation)
        self.setSelectionMoveOffset("", 0.0, 0.0)

    @staticmethod
    def getObservationBounds(shapeType: str, observation: dict):
        """
        Compute the bounding box of a shape observation.

        Args:
            shapeType: the shape type (Point2d, Line2d, Circle, Rectangle).
            observation: the shape observation.

        Returns:
            The (xMin, yMin, xMax, yMax) tuple in image coordinates, or None for an unknown shape type.
        """
        match shapeType:
            case "Point2d":
                return (observation["x"], observation["y"], observation["x"], observation["y"])
            case "Line2d":
                a, b = observation["a"], observation["b"]
                return (min(a["x"], b["x"]), min(a["y"], b["y"]), max(a["x"], b["x"]), max(a["y"], b["y"]))
            case "Circle":
                center, radius = observation["center"], observation["radius"]
                return (center["x"] - radius, center["y"] - radius, center["x"] + radius, center["y"] + radius)
            case "Rectangle":
                center, size = observation["center"], observation["size"]
                halfWidth, halfHeight = size["width"] * 0.5, size["height"] * 0.5
                return (center["x"] - halfWidth, center["y"] - halfHeight, center["x"] + halfWidth, center["y"] + halfHeight)
        return None

    @Slot(float, float, float, float, bool)
    def selectShapesInRect(self, x: float, y: float, width: float, height: float, additive: bool):
        """
        Select the displayed shapes fully inside the given rectangle.

        Args:
            x, y, width, height: the rectangle in image coordinates.
            additive: add the shapes to the current selection instead of replacing it.
        """
        viewId = self._activeProject.selectedViewId
        names = list(self._selectedShapeNames) if additive else []
        for shape in self._getDisplayedShapes():
            bounds = self.getObservationBounds(shape.type, shape.geometry.getObservation(viewId))
            if bounds is None or shape.fullName in names:
                continue
            xMin, yMin, xMax, yMax = bounds
            if xMin >= x and yMin >= y and xMax <= x + width and yMax <= y + height:
                names.append(shape.fullName)
        self.selectedShapeNames = names

    @Slot()
    def selectAllShapes(self):
        """Select all the editable shapes displayed in the 2d Viewer."""
        self.selectedShapeNames = [shape.fullName for shape in self._getDisplayedShapes()]

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
            self._repositioning = False
            self._activeProject.setObservation(shape, viewId, observation)
            self.placementChanged.emit()

    @Slot(float, float, float, float)
    def placeSelectedShapeAt(self, x: float, y: float, visibleWidth: float, visibleHeight: float):
        """
        Place the selected shape at the given image position, sized relative to the visible viewport.
        When repositioning, the current observation is moved instead.
        """
        shapeType = self._getPlacementShapeType()
        if not shapeType:
            return
        shape = self._selectedShape
        if self._repositioning and self._hasCurrentObservation(shape):
            currentObservation = shape.geometry.getObservation(self._activeProject.selectedViewId)
            observation = self.getMovedObservation(shapeType, currentObservation, x, y)
        else:
            observation = self.getObservationAt(shapeType, x, y, visibleWidth, visibleHeight)
        self._placeSelectedShape(observation)

    @Slot(float, float, float, float, result=Variant)
    def getPlacementDragObservation(self, x0: float, y0: float, x1: float, y1: float) -> Variant:
        """Observation of the shape to place defined by a drag from (x0, y0) to (x1, y1), used for the drag preview."""
        return self.getDragObservation(self._getPlacementShapeType(), x0, y0, x1, y1)

    @Slot(float, float, float, float, float, float)
    def placeSelectedShapeFromDrag(self, x0: float, y0: float, x1: float, y1: float,
                                   visibleWidth: float, visibleHeight: float):
        """
        Place the selected shape with the geometry defined by a drag from (x0, y0) to (x1, y1) in image coordinates.
        An empty circle or rectangle falls back to a default shape at the drag start position.
        """
        shapeType = self._getPlacementShapeType()
        if not shapeType:
            return
        observation = self.getDragObservation(shapeType, x0, y0, x1, y1)
        if observation is None:
            observation = self.getObservationAt(shapeType, x0, y0, visibleWidth, visibleHeight)
        self._placeSelectedShape(observation)

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

    selectionMoveChanged = Signal()
    selectionMoveSource = Property(str, lambda self: self._selectionMoveSource, notify=selectionMoveChanged)
    selectionMoveOffset = Property(QPointF, lambda self: self._selectionMoveOffset, notify=selectionMoveChanged)

    placementChanged = Signal()
    isShapeListSelected = Property(bool, _isShapeListSelected, notify=placementChanged)
    isListPlacement = Property(bool, lambda self: self._listPlacement, _setListPlacement, notify=placementChanged)
    isRepositioning = Property(bool, lambda self: self._repositioning, notify=placementChanged)
    isPlacing = Property(bool, _isPlacing, notify=placementChanged)
    placementShapeType = Property(str, _getPlacementShapeType, notify=placementChanged)
