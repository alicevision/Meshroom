from __future__ import print_function

__version__ = "1.2"

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

    def resolvedPaths(self, inputFiles, outDir):
        paths = {}
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                paths[f] = os.path.join(outDir, os.path.basename(f))
        return paths

    def processChunk(self, chunk):
        if not chunk.node.inputFiles:
            chunk.log.add('Nothing to publish', 'warning')
            return
        if not chunk.node.output.value:
            return

        outFiles = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

        if not outFiles:
            error = 'Publish: input files listed, but nothing to publish'
            chunk.log.add(error, 'error')
            chunk.log.add('Listed input files: {}'.format([i.value for i in chunk.node.inputFiles.value]))
            raise RuntimeError(error)

        if not os.path.exists(chunk.node.output.value):
            os.mkdir(chunk.node.output.value)

        for iFile, oFile in outFiles.items():
            chunk.log.add('Publish file {} into {}'.format(iFile, oFile))
            shutil.copyfile(iFile, oFile)
        chunk.log.add('Publish end')
