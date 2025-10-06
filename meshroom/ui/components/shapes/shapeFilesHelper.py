from meshroom.ui.reconstruction import Reconstruction
from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, Slot
from meshroom.core.attribute import GroupAttribute, ListAttribute
from .shapeFile import ShapeFile

class ShapeFilesHelper(BaseObject):
    """
    Manages active project selected node shape files.
    """

    def __init__(self, activeProject:Reconstruction, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._shapeFiles = ListModel()
        self._activeProject.selectedViewIdChanged.connect(self._onSelectedViewIdChanged)
        self._activeProject.selectedNodeChanged.connect(self._onSelectedNodeChanged)

    def _loadShapeFilesFromAttributes(self, attributes):
        """
        Search for File attribute with shape file semantic in selected node attributes.
        Update the model based on the shape files found.
        """
        for attribute in attributes:
            if isinstance(attribute, (ListAttribute, GroupAttribute)):
                self._loadShapeFilesFromAttributes(attribute.value)
            elif attribute.type == "File" and attribute.desc.semantic == "shapeFile":
                self._shapeFiles.append(ShapeFile(fileAttribute=attribute, 
                                                  viewId=self._activeProject.selectedViewId,
                                                  parent=self._shapeFiles))

    @Slot()
    def _onSelectedViewIdChanged(self):
        """Callback when the active project selected view id changes."""
        for shapeFile in self._shapeFiles:
            shapeFile.setViewId(self._activeProject.selectedViewId)

    @Slot()
    def _onSelectedNodeChanged(self):
        """Callback when the active project selected node changes."""
        # clear shapeFiles model
        self._shapeFiles = ListModel()
        # check current node
        if self._activeProject.selectedNode is None:
            return
        # check current node has displayable shape
        if not self._activeProject.selectedNode.hasDisplayableShape:
            return
        # load node shape files
        self._loadShapeFilesFromAttributes(self._activeProject.selectedNode.attributes)
        self.nodeShapeFilesChanged.emit()

    # Properties and signals
    nodeShapeFilesChanged = Signal()
    nodeShapeFiles = Property(Variant, lambda self: self._shapeFiles, notify=nodeShapeFilesChanged)