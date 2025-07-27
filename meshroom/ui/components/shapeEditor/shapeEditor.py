from PySide6.QtCore import QObject, Slot, Property
from meshroom.ui.reconstruction import Reconstruction
from .shapeListModel import ShapeListModel
from .shapeFileListModel import ShapeFileListModel
import os

class ShapeEditor(QObject):
    """Controller to manage interactions between qml and the current node shapes data models."""

    def __init__(self, activeProject:Reconstruction, parent=None):
        super().__init__(parent)
        self._enable = False
        self._activeProject = activeProject
        # build empty models
        self._currentNodeShapeList = ShapeListModel(name="Node Parameters", currentViewId=self._activeProject.selectedViewId, parent=self)
        self._currentNodeFileShapeLists = ShapeFileListModel(currentViewId=self._activeProject.selectedViewId, parent=self)

    @Property(type=QObject, constant=True)
    def nodeShapeList(self):
        """Expose the current node shape list model to qml."""
        return self._currentNodeShapeList
    
    @Property(type=QObject, constant=True)
    def nodeFileShapeLists(self):
        """Expose the current node output files shape lists model to qml."""
        return self._currentNodeFileShapeLists
    
    @Slot(bool)
    def enable(self, enable: bool): 
        """Enable / Disable the ShapeEditor"""
        # check ShapeEditor enable state
        if enable == self._enable:
            return
        # connect active project update signals
        # build or clear the models
        if enable:
            self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
            self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)
            self._onSelectedViewIdChanged()
            self._onSelectedViewIdChanged()
        else :
            self._activeProject.selectedViewIdChanged.disconnect(self._onSelectedViewIdChanged)
            self._activeProject.selectedNodeChanged.disconnect(self._onSelectedNodeChanged)
            self._currentNodeShapeList.clear()
            self._currentNodeFileShapeLists.clear()
        self._enable = enable  

    @Slot()
    def _onSelectedViewIdChanged(self):
        """Callback when the active project selected view id changes."""
        # update node shape list
        self._currentNodeShapeList.setCurrentViewId(self._activeProject.selectedViewId)
        # update node shape file lists
        self._currentNodeFileShapeLists.setCurrentViewId(self._activeProject.selectedViewId)

    @Slot()
    def _onSelectedNodeChanged(self):
        """Callback when the active project selected node changes."""
        # check selected node is valid
        if self._activeProject.selectedNode is None:
            return
        # connect node changed signal
        # TODO: find better update signal, at attribute level
        # TODO: disconnect
        self._activeProject.selectedNode.internalAttributesChanged.connect(self._onSelectedNodeChanged)
        # load node parameters shapes
        self._currentNodeShapeList.loadShapesFromNode(self._activeProject.selectedNode)
        # find node shape file parameters
        self._currentNodeFileShapeLists.clear()
        nodeShapeFileNames = []
        for attribute in self._activeProject.selectedNode.attributes:
            self.__getShapeFiles(attribute, nodeShapeFileNames)
        print(nodeShapeFileNames) # TODO: Remove
        # load node shape file parameters
        for filepath in nodeShapeFileNames:
            self._currentNodeFileShapeLists.addShapeListFile(name=os.path.basename(filepath), filepath=filepath)

    def __getShapeFiles(self, attribute, list):
        # check if the attribute is a shape attribute
        if not attribute.desc.semantic == "shapesFile":
            # recusive call if ListAttribute or GroupAttribute
            if attribute.type == "ListAttribute" or attribute.type == "GroupAttribute":
                for childAttribute in attribute.value:
                    self.__getShapeFiles(childAttribute, list)
            return
        # check if the shape file exists  
        if os.path.exists(attribute.value):     
            list.append(attribute.value)