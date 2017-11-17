from __future__ import print_function
from meshroom.core import desc
import shutil
import glob
import os


class Publish(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')
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

    def processChunk(self, chunk):
        print("Publish")
        if not chunk.node.inputFiles:
            print("Nothing to publish")
            return
        if not chunk.node.output.value:
            return

        inputFiles = []
        for inputFile in chunk.node.inputFiles:
            iFiles = glob.glob(inputFile.value)
            inputFiles.extend(iFiles)
        if not inputFiles:
            raise RuntimeError("Publish: input files listed, but nothing to publish. Listed input files: {}".format(node.inputFiles))

        if not os.path.exists(chunk.node.output.value):
            os.mkdir(chunk.node.output.value)

        for iFile in inputFiles:
            filename = os.path.basename(iFile)
            oFile = os.path.join(chunk.node.output.value, filename)
            print('Publish file', iFile, 'into', oFile)
            shutil.copyfile(iFile, oFile)
        print('Publish end')
