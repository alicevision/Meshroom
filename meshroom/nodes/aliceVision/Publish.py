from __future__ import print_function

__version__ = "1.1"

from meshroom.core import desc
import shutil
import glob
import os


class Publish(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')

    category = 3
    info = "A node"
    
    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input",
                description="",
                value="",
                uid=[0],
            ),
            name="inputFiles",
            label="Input Files",
            description="Input Files to publish.",
            group="",
        ),
        desc.File(
            name="output",
            label="Output Folder",
            description="",
            value="",
            uid=[0],
            ),
        ]

    def resolvedPaths(self, inputFiles, outDir):
        paths = {}
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                paths[f] = os.path.join(outDir, os.path.basename(f))
        return paths

    def processChunk(self, chunk):
        print("Publish")
        if not chunk.node.inputFiles:
            print("Nothing to publish")
            return
        if not chunk.node.output.value:
            return

        outFiles = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

        if not outFiles:
            raise RuntimeError("Publish: input files listed, but nothing to publish. "
                               "Listed input files: {}".format(chunk.node.inputFiles.value))

        if not os.path.exists(chunk.node.output.value):
            os.mkdir(chunk.node.output.value)

        for iFile, oFile in outFiles.items():
            print('Publish file', iFile, 'into', oFile)
            shutil.copyfile(iFile, oFile)
        print('Publish end')
