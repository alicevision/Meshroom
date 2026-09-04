from typing import ClassVar, List

from meshroom.core import desc


class OutputNodeTest(desc.Node, desc.OutputNode):
    outputAttributes: ClassVar[List[str]] = ["folder", "outputFile", "exportLabel", "exportEnabled"]

    inputs = [
        desc.File(
            name="folder",
            label="Folder",
            description="Output folder.",
            value="/default/output",
        ),
        desc.File(
            name="outputFile",
            label="File",
            description="Secondary output path.",
            value="",
        ),
        desc.StringParam(
            name="exportLabel",
            label="Label",
            description="Export label.",
            value="default",
        ),
        desc.BoolParam(
            name="exportEnabled",
            label="Enabled",
            description="Export enabled.",
            value=True,
        ),
        desc.StringParam(
            name="internalLabel",
            label="Internal Label",
            description="Internal label.",
            value="internal",
        ),
    ]
    outputs = []
