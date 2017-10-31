from __future__ import print_function
from meshroom.core import desc
import shutil
import glob
import os


class Publish(desc.Node):
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

    def process(self, node):
        print("Publish")
        if not node.inputFiles:
            print("Nothing to publish")
            return
        if not node.output.value:
            return

        inputFiles = []
        for inputFile in node.inputFiles:
            iFiles = glob.glob(inputFile.value)
            inputFiles.extend(iFiles)
        if not inputFiles:
            raise RuntimeError("Publish: input files listed, but nothing to publish. Listed input files: {}".format(node.inputFiles))

        if not os.path.exists(node.output.value):
            os.mkdir(node.output.value)

        for iFile in inputFiles:
            filename = os.path.basename(iFile)
            oFile = os.path.join(node.output.value, filename)
            print('Publish file', iFile, 'into', oFile)
            shutil.copyfile(iFile, oFile)
        print('Publish end')
