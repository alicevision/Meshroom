from meshroom.nodes.aliceVision.Meshing import boundingBoxMonitor
from meshroom.core.node import Node
from meshroom.common import Property, Signal

class MeshingNode(Node):
    def __init__(self, nodeType, position=None, parent=None, **kwargs):
        super().__init__(nodeType, position, parent, **kwargs)
        self.internalFolderChanged.connect(self.checkBBox)
        self.globalStatusChanged.connect(self.checkBBox)
        self._automaticBBoxValid = False

    @property
    def automaticBBoxValid(self):
        return self._automaticBBoxValid
    
    @automaticBBoxValid.setter
    def automaticBBoxValid(self, value):
        self._automaticBBoxValid = value
        self.automaticBBoxValidChanged.emit()

    automaticBBoxValidChanged = Signal()
    automaticBBoxValid = Property(bool, automaticBBoxValid.fget, automaticBBoxValid.fset, notify=automaticBBoxValidChanged)

    def checkBBox(self):
        """Load automatic bounding box if needed."""
        if self.useBoundingBox.value:
            return
        self.automaticBBoxValid = False
        with boundingBoxMonitor(self, checkOnce=True) as thread:
            pass
