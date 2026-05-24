__version__ = "1.0"

from meshroom.core import desc


class FlattenFiles(desc.Node):
    """
    This node takes a list of lists of files as input and produces a single flat list of
    files as output.

    It is useful to merge multiple file lists coming from different nodes into a unified
    list, for example before passing them to a node that expects a flat list.
    """

    category = "Utils"

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.ListAttribute(
                elementDesc=desc.File(
                    name="file",
                    label="File",
                    description="An input file.",
                    value="",
                ),
                name="fileList",
                label="File List",
                description="An input list of files.",
            ),
            name="inputFiles",
            label="Input Files",
            description="Input list of lists of files to flatten into a single list.",
            exposed=True,
        ),
    ]

    outputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="outputFile",
                label="File",
                description="An output file.",
                value="",
            ),
            name="outputFiles",
            label="Output Files",
            description="Output flat list of all files from the input lists.",
            value=None,
            exposed=True,
        ),
    ]

    def process(self, node):
        flatFiles = []
        for fileList in node.inputFiles.value:
            for fileAttr in fileList.value:
                flatFiles.append(fileAttr.value)
        node.outputFiles.value = flatFiles
