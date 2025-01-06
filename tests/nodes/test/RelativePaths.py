from meshroom.core import desc

class RelativePaths(desc.Node):
    documentation = "Test node with filepaths that are set relatively to some variables."
    inputs = [
        desc.File(
            name="relativePathInput",
            label="Relative Input File",
            description="Relative path to the input file.",
            value="${NODE_SOURCECODE_FOLDER}" + "/input.txt",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output file.",
            value="${NODE_CACHE_FOLDER}" + "file.out",
        ),
    ]

    def processChunk(self, chunk):
        pass
