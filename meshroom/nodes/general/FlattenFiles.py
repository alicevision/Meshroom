__version__ = "1.0"

from meshroom.core import desc


class FlattenFiles(desc.Node):
    """
    Utility conversion node that flattens a list of lists of files into a single list of files.
    """

    category = "Utils"
    documentation = """
This node takes a list of lists of files as input and produces a single flat list of files as output.

It is useful to merge multiple file lists coming from different nodes into a unified list,
for example before passing them to a node that expects a flat list.
"""

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.ListAttribute(
                elementDesc=desc.File(
                    name="file",
                    label="File",
                    description="A file.",
                    value="",
                ),
                name="fileList",
                label="File List",
                description="A list of files.",
            ),
            name="inputFiles",
            label="Input Files",
            description="List of lists of files to flatten into a single list.",
            exposed=True,
        ),
    ]

    outputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="file",
                label="File",
                description="A file.",
                value="",
            ),
            name="outputFiles",
            label="Output Files",
            description="Flat list of all files from the input lists.",
            exposed=True,
        ),
    ]

    def process(self, node):
        flatFiles = []
        for fileList in node.inputFiles.value:
            for fileAttr in fileList.value:
                flatFiles.append(fileAttr.value)
        node.outputFiles.value = flatFiles
