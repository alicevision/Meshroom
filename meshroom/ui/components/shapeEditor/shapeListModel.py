from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot
from PySide6.QtGui import QColor
from meshroom.core.attribute import Attribute
from .shapeData import ShapeData
import json

class ShapeListModel(QAbstractListModel):
    """List template to expose shape data to qml."""

    # data roles
    ModelIndexRole = Qt.UserRole + 1   # model index of the shape
    ShapeNameRole = Qt.UserRole + 2    # shape name
    ShapeTypeRole = Qt.UserRole + 3    # shape type (point, line, circle, etc.)
    PropertiesRole = Qt.UserRole + 4   # shape properties dictionary
    ObservationRole = Qt.UserRole + 5  # shape observation dictionary
    IsEditableRole = Qt.UserRole + 6   # shape is editable
    IsVisibleRole = Qt.UserRole + 7    # shape is visible

    def __init__(self, name, currentViewId="-1", filepath=None, parent=None):
        super().__init__(parent)
        self._shapes = []
        self._name = name
        self._currentViewId = currentViewId
        # populate the model from a file, if provided
        if filepath is not None:
            self.loadShapesFromJsonFile(filepath)
    
    def getName(self):
        """Get the name of the ShapeListModel."""
        return self._name
    
    def setName(self, name):
        """Set the name of the ShapeListModel."""
        self._name = name
        
    def setCurrentViewId(self, viewId):
        """Set the current view id and update the model."""
        # check none or same view id 
        if viewId is None or self._currentViewId == viewId:
            return
        self.beginResetModel() # begin reset model
        self._currentViewId = viewId
        self.endResetModel() # end reset model

    def loadShapesFromJsonFile(self, filepath):
        """Load the shape list from the given json file."""
        self.beginResetModel() # begin reset model
        self._shapes.clear()   # clear model
        try:
            with open(filepath, "r") as f:
                loadedData = json.load(f)
                for itemData in loadedData:
                    name = itemData.get("name", "unknown")
                    type = itemData.get("type", "unknown")
                    properties = itemData.get("properties", {})
                    observations = itemData.get("observations", {})
                    self._shapes.append(ShapeData(name, type, properties, observations, isStatic=(len(observations)<=0), isEditable=False))
        except FileNotFoundError:
            print("No shapes found to load.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error loading shapes: {e}")
        self.endResetModel() # end reset model

    def loadShapesFromNode(self, node):
        """Load the shape list from from the given node."""
        self.beginResetModel() # begin reset model
        self._shapes.clear()   # clear model
        # if current node is defined
        # build and append a shape for each node shape attribute
        if node is not None:
            for attribute in node.attributes:
                self.__buildCurrentNodeShape(attribute)
        self.endResetModel() # end reset model

    def __buildCurrentNodeShape(self, attribute:Attribute):
        """Recursively builds the shape(s) of the given attribute."""
        # check if the attribute is a shape attribute
        if not attribute.is2DShape:
            # recusive call if ListAttribute or GroupAttribute
            if attribute.type == "ListAttribute" or attribute.type == "GroupAttribute":
                for childAttribute in attribute.value:
                    self.__buildCurrentNodeShape(childAttribute)
            return
        shape = self.__buildShapeFromAttribute(attribute) # build shape
        if shape is not None:
            self._shapes.append(shape)

    def __buildShapeFromAttribute(self, shapeAttribute:Attribute):
        """Build and return the shape data of the given attribute."""
        # check shapeAttribute is defined
        if shapeAttribute is None:
            return None
        # check if the attribute is a shape attribute
        if not shapeAttribute.is2DShape:
            return None
        # check shape attribute type 
        if shapeAttribute.type != "GroupAttribute":
            return None
        # build shape properties/observations from child attributes
        properties = {}
        observations = {}
        isStatic = True
        for attribute in shapeAttribute.value:
            if attribute.name == "hue":
                properties["color"] = QColor.fromHslF(attribute.value, 1, 0.5, a=1.0).name(QColor.HexArgb)
            if attribute.type == "ListAttribute":
                isStatic = False
                for observationAttribute in attribute.value:
                    observation = {}
                    for propertyAttribute in observationAttribute.value:
                        observation[propertyAttribute.name] = propertyAttribute.value
                    observations[str(observation.get("viewId", -1))] = observation
        # add the new shape
        return ShapeData(name=shapeAttribute.name, type=shapeAttribute.desc.semantic, properties=properties, observations=observations, isStatic=isStatic)
    
    def clear(self):
        """Clear all ths shapes and update the model."""
        self.beginResetModel() # begin reset model
        self._shapes.clear()
        self.endResetModel() # end reset model
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._shapes)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._shapes)):
            return None
        shape = self._shapes[index.row()]
        match role:
            case self.ModelIndexRole:
                # Return the model index of the shape
                return index.row() 
            case self.ShapeNameRole:
                # Return the shape name
                return shape.name    
            case self.ShapeTypeRole:
                # Return the shape type (point, line, circle, etc.)
                return shape.type    
            case self.PropertiesRole:
                # Return the shape properties dictionary
                return shape.properties   
            case self.ObservationRole:
                # Return the shape observation dictionary  
                return shape.getObservation(self._currentViewId)  
            case self.IsEditableRole:
                # Return true if the shape is editable
                return shape.isEditable
            case self.IsVisibleRole:
                # Return true if the shape is visible
                return shape.isVisible
        return None

    def roleNames(self):
        roles = {}
        roles[self.ModelIndexRole] = b"modelIndex"
        roles[self.ShapeNameRole] = b"shapeName"
        roles[self.ShapeTypeRole] = b"shapeType"
        roles[self.PropertiesRole] = b"properties"
        roles[self.ObservationRole] = b"observation"
        roles[self.IsEditableRole] = b"isEditable"
        roles[self.IsVisibleRole] = b"isVisible"
        return roles
    
    @Slot(int, bool)
    def updateShapeVisibility(self, modelIndex, visible):
        """Updates an existing shape visibility."""
        # check modelIndex is correct
        if not (0 <= modelIndex < len(self._shapes)):
            return
        # set shape visibility
        self._shapes[modelIndex].isVisible = visible
        # notifies qml of changes to update the view
        self.dataChanged.emit(self.index(modelIndex), self.index(modelIndex), [self.IsVisibleRole])