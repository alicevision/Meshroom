__version__ = "1.0"

import os
import logging
from meshroom.core import desc


class Resection(desc.Node):
    
    category = "Other"

    inputs = [
        desc.File(
            name="file",
            label="File",
            description="File or Folder.",
            exposed=True,
            value=""
        ),

        desc.ShapeList(
            name="keyablePointList",
            label="Keyable Point 3d List",
            description="Keyable point 3d list.",
            shape=desc.Point3d(
                name="point",
                label="Point",
                description="A 3d point.",
                keyable=True,
                keyType="viewId"
            ),
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="output",
            value=None,
        )
    ]

    def process(self, node):
        node.folder.value = ""
        path = node.file.value
        if not path:
            return
        # Additional security but it's supposedly handeled by the validator
        path = os.path.normpath(path)
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            logging.warning(f"Parent path {parent} does not exist")
        node.folder.value = parent
