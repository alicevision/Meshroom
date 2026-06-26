from meshroom.core import desc

class InitDynamicOutputs(desc.InitNode):
    inputs = [
        desc.File(
            name="fileInput",
            label="File Input",
            description="A file input.",
            value="testFile",
        ),
    ]

    outputs = [
        desc.File(
            name="fileOutput",
            label="File Output",
            description="A file Output.",
            value=None,
        ),
    ]
