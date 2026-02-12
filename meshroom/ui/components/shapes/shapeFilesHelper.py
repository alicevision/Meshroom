from meshroom.ui.scene import Scene
from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, Slot
from meshroom.core.attribute import GroupAttribute, ListAttribute
from shiboken6 import isValid
from .shapeFile import ShapeFile

# Filter runtime warning when closing Meshroom with active shape files
import warnings
warnings.filterwarnings("ignore", message=".*Failed to disconnect.*", category=RuntimeWarning)

class ShapeFilesHelper(BaseObject):
    """
    Manages active project selected node shape files.
    """

    def __init__(self, activeProject:Scene, parent=None):
        super().__init__(parent)
        self._activeProject = activeProject
        self._currentNode = activeProject.selectedNode
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
    def _loadShapeFiles(self):
        """Load/Reload active project selected node shape files."""
        # clear shapeFiles model
        self._shapeFiles.clear()
        # load node shape files
        if self._activeProject.selectedNode:
            self._loadShapeFilesFromAttributes(self._activeProject.selectedNode.attributes)
        self.nodeShapeFilesChanged.emit()

    @Slot()
    def _onSelectedViewIdChanged(self):
        """Callback when the active project selected view id changes."""
        for shapeFile in self._shapeFiles:
            shapeFile.setViewId(self._activeProject.selectedViewId)

    @Slot()
    def _onSelectedNodeChanged(self):
        """Callback when the active project selected node changes."""
        # disconnect internalFolderChanged signal
        if self._currentNode is not None:
            try:
                self._currentNode.internalFolderChanged.disconnect(self._loadShapeFiles)
            except RuntimeError:
                # Signal was already disconnected or never connected
                pass
        # check selected node exists and selected node has displayable shape
        if self._activeProject.selectedNode is None or not self._activeProject.selectedNode.hasDisplayableShape:
            # clear shapeFiles model
            if isValid(self._shapeFiles):
                self._shapeFiles.clear()
            # clear current node
            self._currentNode = None
            return
        # update current node
        self._currentNode = self._activeProject.selectedNode
        # connect internalFolderChanged signal
        try:
            self._currentNode.internalFolderChanged.connect(self._loadShapeFiles)
        except RuntimeError:
            # Signal was already disconnected or never connected
            pass
        # load node shape files
        self._loadShapeFiles()

    # Properties and signals
    nodeShapeFilesChanged = Signal()
    nodeShapeFiles = Property(Variant, lambda self: self._shapeFiles, notify=nodeShapeFilesChanged)