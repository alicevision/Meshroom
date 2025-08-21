from PySide6.QtCore import QObject, Slot, Property
from meshroom.core.attribute import Attribute
from meshroom.ui.reconstruction import Reconstruction
from .shapeListModel import ShapeListModel
from .shapeNodeModel import ShapeNodeModel

class ShapeEditor(QObject):
    """Controller to manage interactions between qml and the current node shapes data models."""

    def __init__(self, activeProject:Reconstruction, parent=None):
        super().__init__(parent)
        self._enable = False
        self._currentNode = None
        self._activeProject = activeProject
        self._currentNodeShapeLists = ShapeNodeModel(currentViewId=self._activeProject.selectedViewId, parent=self)

    @Property(type=QObject, constant=True)
    def nodeShapeLists(self):
        """Expose the current node shape lists model to qml."""
        return self._currentNodeShapeLists
    
    @Slot(bool)
    def enable(self, enable: bool): 
        """Enable / Disable the ShapeEditor"""
        # check ShapeEditor enable state
        if enable == self._enable:
            return
        # connect active project update signals
        # build or clear the models
        if enable:
            # connect project signals
            self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
            self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)
            self._onSelectedViewIdChanged() # force view Id update
            self._onSelectedNodeChanged() # force current node update
        else :
            # disconnect project signals
            self._activeProject.selectedViewIdChanged.disconnect(self._onSelectedViewIdChanged)
            self._activeProject.selectedNodeChanged.disconnect(self._onSelectedNodeChanged)
            self._currentNodeShapeLists.clear() # clear model
        self._enable = enable  

    @Slot()
    def _onSelectedViewIdChanged(self):
        """Callback when the active project selected view id changes."""
        # update node shape lists
        self._currentNodeShapeLists.setCurrentViewId(self._activeProject.selectedViewId)

    @Slot()
    def _onSelectedNodeChanged(self):
        """Callback when the active project selected node changes."""
        # disconnect previous current node changed signal
        if self._currentNode is not None:
            self._currentNode.internalsUpdated.disconnect(self._onSelectedNodeChanged)
        # update current node
        self._currentNode = self._activeProject.selectedNode
        # check current node is valid
        if self._currentNode is None:
            return
        # connect current node changed signal
        self._activeProject.selectedNode.internalsUpdated.connect(self._onSelectedNodeChanged)
        # load node shape parameters and files
        self._currentNodeShapeLists.loadFromNode(self._activeProject.selectedNode)

    def __getShapeObservationsAttribute(self, shapeName:str) -> Attribute:
        """Get the observations attribute of the given shape."""
        # check shapeName and current node
        if shapeName is None or self._currentNode is None:
            return None
        # get current node shape attribute
        attribute = self._currentNode.attribute(shapeName)
        # check shape attribute
        if attribute is None and attribute.type != "GroupAttribute":
            return None
        # get observation list attribute
        listAttribute = None
        for childAttribute in attribute.value:
            if childAttribute.type == "ListAttribute":
                listAttribute = childAttribute
        return listAttribute

    def __getShapeCurrentObservationAttribute(self, shapeName:str) -> Attribute:
        """Get the current observation attribute of the given shape."""
        # get shape observations list attribute
        observationsAttribute = self.__getShapeObservationsAttribute(shapeName)
         # check shape observations list attribute
        if observationsAttribute is None:
            return None
        # find observation group attribute
        for attribute in observationsAttribute:
            viewIdAttribute = attribute.childAttribute("viewId")
            if viewIdAttribute is not None and str(viewIdAttribute.value) == self._activeProject._selectedViewId:
                return attribute
        # no observation found
        return None

    @Slot(str)
    def addCurrentObservation(self, shapeName:str):
        """Add the current view id observation for the given shape."""
        # get shape observations list attribute
        observationsAttribute = self.__getShapeObservationsAttribute(shapeName)
        # check shape observations list attribute
        if observationsAttribute is None:
            return
        # add current observation
        self._activeProject.appendAttribute(observationsAttribute, "{\"viewId\": " + self._activeProject._selectedViewId + "}")

    @Slot(str)
    def removeCurrentObservation(self, shapeName:str):
        """Remove the current view id observation for the given shape."""
        # get shape current observation group attribute
        observationAttribute = self.__getShapeCurrentObservationAttribute(shapeName)
        # check shape current observation group attribute
        if observationAttribute is None:
            return
        # remove current observation
        self._activeProject.removeAttribute(observationAttribute)