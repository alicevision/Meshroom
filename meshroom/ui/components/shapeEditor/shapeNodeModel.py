from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from .shapeListModel import ShapeListModel
import os

class ShapeNodeModel(QAbstractListModel):
    """List template to expose multiple ShapeListModel to qml."""

    # data roles
    ModelIndexRole = Qt.UserRole + 1      # model index of the shape list
    ShapeListNameRole = Qt.UserRole + 2   # name of the shape list
    ShapeListModelRole = Qt.UserRole + 3  # shape list model

    def __init__(self, currentViewId="-1", parent=None):
        super().__init__(parent)
        self._shapeLists = []
        self._currentViewId = currentViewId

    def setCurrentViewId(self, viewId):
        """Set the current view id and update the model."""
        # check none or same view id 
        if viewId is None or self._currentViewId == viewId:
            return
        self.beginResetModel() # begin reset model
        self._currentViewId = viewId
        for shapeList in  self._shapeLists:
            shapeList.setCurrentViewId(self._currentViewId)
        self.endResetModel() # end reset model

    def loadFromNode(self, node):
        """Load shape lists from the given node."""
        self.beginResetModel() # begin reset model
        # clear previous shape lists
        self._shapeLists.clear()
        # load node shape parameters 
        nodeShapeList = ShapeListModel(name="Node Parameters", currentViewId=self._currentViewId, parent=self)
        nodeShapeList.loadShapesFromNode(node)
        self._shapeLists.append(nodeShapeList)
        # load node shape files
        for attribute in node.attributes:
            self.__buildFileShapeListFromAttribute(attribute)
        self.endResetModel() # end reset model

    def __buildFileShapeListFromAttribute(self, attribute):
        """Recursively builds the json file(s) shape list(s) from the given attribute."""
        # check if the attribute is a shape attribute
        if not attribute.desc.semantic == "shapesFile":
            # recusive call if ListAttribute or GroupAttribute
            if attribute.type == "ListAttribute" or attribute.type == "GroupAttribute":
                for childAttribute in attribute.value:
                    self.__buildFileShapeListFromAttribute(childAttribute)
            return
        # check if the shape file exists  
        if os.path.exists(attribute.value):     
            self._shapeLists.append(ShapeListModel(name=os.path.basename(attribute.value), currentViewId=self._currentViewId, filepath=attribute.value, parent=self))

    def clear(self):
        """Clear all ths ShapeLists and update the model."""
        self.beginResetModel() # begin reset model
        self._shapeLists.clear()
        self.endResetModel() # end reset model

    def rowCount(self, parent=QModelIndex()):
        return len(self._shapeLists)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._shapeLists)):
            return None
        shapeList = self._shapeLists[index.row()]
        match role:
            case self.ModelIndexRole:
                # Return the model index of the shape
                return index.row() 
            case self.ShapeListNameRole:
                # Return the shape list name
                return shapeList.getName()
            case self.ShapeListModelRole:
                # Return the shape list model
                return shapeList   
        return None

    def roleNames(self):
        roles = {}
        roles[self.ModelIndexRole] = b"modelIndex"
        roles[self.ShapeListNameRole] = b"shapeListName"
        roles[self.ShapeListModelRole] = b"shapeListModel"
        return roles