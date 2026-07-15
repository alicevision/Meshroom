__version__ = "1.0"

import os
from meshroom.core import desc


class GetFileExtension(desc.InlineNode):
    inputs = [
        desc.File(
            name="path",
            value="",
            exposed=True,
        ),
    ]

    outputs = [
        desc.StringParam(
            name="extension",
            value=None,
        ),
    ]

    def process(self, node):
        if not node.path.value:
            node.extension.value = ""
        else:
            node.extension.value = os.path.splitext(node.path.value)[1]
