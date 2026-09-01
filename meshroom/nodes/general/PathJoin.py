__version__ = "1.0"

import os
from meshroom.core import desc


class PathJoin(desc.InlineNode):
    """ Join multiple paths """
    
    category = "Other"

    inputs = [
        desc.ListAttribute(
            name="paths",
            description="Paths to join.",
            exposed=True,
            elementDesc=desc.StringParam(
                name="path",
                exposed=True,
                value=""
            )
        ),
        desc.BoolParam(
            name="checkIfExists",
            description="Check if the output path exists. If it doesn't, the output will be an empty string.",
            value=False,
        )
    ]

    outputs = [
        desc.File(
            name="outputPath",
            label="Path",
        )
    ]
    
    def process(self, node):
        parts = []
        for item in node.paths.value:
            path = item.value
            if path:
                parts.append(path)
        if parts:
            outputPath = os.path.join(*parts)
            if not node.checkIfExists.value or os.path.exists(outputPath):
                node.outputPath.value = str(outputPath)
                return
        node.folder.value = ""
