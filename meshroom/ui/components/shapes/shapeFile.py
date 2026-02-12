from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, Slot
from meshroom.core.attribute import Attribute
import json, os, re

class ShapeFile(BaseObject):
    """
    List of shapes provided by a json file attribute.
    """

    class ShapeData(BaseObject):
        """
        Single shape with its properties and observations.
        """
        def __init__(self, name: str, type: str, properties={}, observations={}, parent=None):
            super().__init__(parent)
            # View id
            self._viewId = "-1"
            # Shape name
            self._name = name
            # Shape type (Point2d, Line2d, Rectangle, Circle, etc.)
            self._type = type
            # Shape properties (color, stroke, etc.)
            self._properties = properties
            # Shape observations {viewId: observation{x, y, radius, etc.}}
            self._observations = observations
            # Shape keyabale
            self._keyable = len(observations) > 0
            # Shape visible
            self._visible = True

        def _getVisible(self) -> bool:
            """
            Return whether the shape is visible for display.
            """
            return self._visible

        def _setVisible(self, visible:bool):
            """
            Set the shape visibility for display.
            """
            self._visible = visible
            self.visibleChanged.emit()

        def setViewId(self, viewId: str):
            """
            Set the shape current view id.
            """
            self._viewId = viewId
            self.viewIdChanged.emit()

        def _getObservation(self):
            """
            Get the shape current observation.
            """
            if self._keyable:
                return self._observations.get(self._viewId, None)
            return self._properties

        def _getNbObservations(self):
            """
            Return the shape number of observations.
            """
            if self._keyable:
                return len(self._observations)
            return 1

        @Slot(str, result=bool)
        def hasObservation(self, key: str) -> bool:
            """
            Return whether the shape has an observation for the given key.
            """
            if self._keyable:
                return self._observations.get(self._viewId, None) is not None
            return True

        # Signals
        viewIdChanged = Signal()
        visibleChanged = Signal()

        # Properties
        # The shape name.
        name = Property(str, lambda self: self._name, constant=True)
        # The shape label.
        label = Property(str, lambda self: self._name, constant=True)
        # The shape type (Point2d, Line2d, Rectangle, Circle, etc.).
        type = Property(str, lambda self: self._type, constant=True)
        # The shape properties (color, stroke, etc.).
        properties = Property(Variant, lambda self: self._properties, constant=True)
        # The shape current observation.
        observation = Property(Variant, _getObservation, notify=viewIdChanged)
        # Whether the shape is keyabale (multiple observations).
        observationKeyable = Property(bool,lambda self: self._keyable, constant=True)
        # The shape list of observation keys.
        observationKeys = Property(Variant, lambda self: [key for key in self._observations], constant=True)
        # The number of observation defined.
        nbObservations = Property(int, _getNbObservations, constant=True)
        # Whether the shape is displayable.
        isVisible = Property(bool, _getVisible, _setVisible, notify=visibleChanged)

    def __init__(self, fileAttribute: Attribute, viewId: str, parent=None):
        super().__init__(parent)
        # List of shapes
        self._shapes = ListModel(parent=self)
        # File attribute
        self._fileAttribute = fileAttribute
        # Current view id
        self._viewId = viewId
        # Shapes visible
        self._visible = True
        # Populate the model from the provided file
        self._loadShapesFromJsonFile()
        # Update viewId for all shapes
        self.setViewId(viewId)
        # Connect file attribute value
        fileAttribute.valueChanged.connect(self._loadShapesFromJsonFile)

    def _getVisible(self) -> bool:
        """
        Return whether the shape file is visible for display.
        """
        return self._visible

    def _setVisible(self, visible:bool):
        """
        Set the shape file visibility for display.
        """
        self._visible = visible
        for shape in self._shapes:
            shape.isVisible = visible
        self.visibleChanged.emit()

    def _getBasename(self) -> str:
        """
        Get file attribute basename.
        """
        return os.path.basename(self._fileAttribute.value)

    def setViewId(self, viewId: str):
        """
        Set the current view id for all shapes of the file.
        """
        for shape in self._shapes:
            shape.setViewId(viewId)

    @Slot()
    def _loadShapesFromJsonFile(self):
        """
        Load shapes from the json file.
        """
        def convertNumericStrings(obj):
            """
            Helper function to convert numeric strings.
            """
            if isinstance(obj, dict):
                return {k: convertNumericStrings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convertNumericStrings(elem) for elem in obj]
            elif isinstance(obj, str):
                # Check for int or float
                if re.fullmatch(r'-?\d+', obj):
                    return int(obj)
                elif re.fullmatch(r'-?\d+\.\d*', obj):
                    return float(obj)
            return obj

        # Clear model
        self._shapes.clear()
        # Load from json file
        if os.path.exists(self._fileAttribute.value):
            try:
                with open(self._fileAttribute.value, "r") as f:
                    # Load json
                    loadedData = json.load(f)
                    # Handle both formats: direct array or object with "shapes" key
                    if isinstance(loadedData, dict) and "shapes" in loadedData:
                        shapesArray = loadedData["shapes"]
                    elif isinstance(loadedData, list):
                        shapesArray = loadedData
                    else:
                        print("Invalid JSON format: expected array or object with 'shapes' key")
                        self.fileChanged.emit()
                        return
                    # Build shapes from proper shapes array
                    for itemData in convertNumericStrings(shapesArray):
                        name = itemData.get("name", "unknown")
                        type = itemData.get("type", "unknown")
                        properties = itemData.get("properties", {})
                        observations = itemData.get("observations", {})
                        self._shapes.append(ShapeFile.ShapeData(name, type, properties, observations, self._shapes))
            except FileNotFoundError:
                print("No shapes found to load.")
            except json.JSONDecodeError as err:
                print(f"Error decoding JSON: {err}")
            except Exception as exc:
                print(f"Error loading shapes: {exc}")
        self.fileChanged.emit()

    # Signals
    fileChanged = Signal()
    visibleChanged = Signal()

    # Properties
    # The model type, always ShapeFile.
    type = Property(str, lambda self: "ShapeFile", constant=True)
    # The corresponding File attribute label.
    label = Property(str, lambda self: self._fileAttribute.label, constant=True)
    # The file basename.
    basename = Property(str, _getBasename, notify=fileChanged)
    # The list of shapes.
    shapes = Property(Variant, lambda self: self._shapes, notify=fileChanged)
    # Whether the file has shapes.
    isEmpty = Property(bool, lambda self: len(self._shapes) <= 0, notify=fileChanged)
    # Whether the file is displayable.
    isVisible = Property(bool, _getVisible, _setVisible, notify=visibleChanged)