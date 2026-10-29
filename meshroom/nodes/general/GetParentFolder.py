__version__ = "1.0"

import os
import logging
from meshroom.core import desc


class GetParentFolder(desc.InlineNode):
    """ Get the parent folder """
    
    category = "Other"

    inputs = [
        desc.File(
            name="file",
            label="File",
            description="File or Folder.",
            exposed=True,
            value=""
        ),
    ]

    outputs = [
        desc.File(
            name="folder",
            label="Folder",
            description="Parent folder.",
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
