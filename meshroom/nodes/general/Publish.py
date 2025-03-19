__version__ = "1.3"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import distutils.dir_util as du
import shutil
import glob
import os


class Publish(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')

    category = 'Export'
    documentation = '''
This node allows to copy files into a specific folder.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input",
                description="File or folder to publish.",
                value="",
            ),
            name="inputFiles",
            label="Input Files",
            description="Input files or folders' content to publish.",
            exposed=True,
            group="",
        ),
        desc.File(
            name="output",
            label="Output Folder",
            description="Folder to publish to.",
            value="",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    def resolvedPaths(self, inputFiles, outDir):
        paths = {}
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                if os.path.isdir(f):
                    paths[f] = outDir  # Do not concatenate the input folder's name with the output's
                else:
                    paths[f] = os.path.join(outDir, os.path.basename(f))
        return paths

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            
            if not chunk.node.inputFiles:
                chunk.logger.warning('Nothing to publish')
                return
            if not chunk.node.output.value:
                return

            outFiles = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

            if not outFiles:
                error = 'Publish: input files listed, but nothing to publish'
                chunk.logger.error(error)
                chunk.logger.info('Listed input files: {}'.format([i.value for i in chunk.node.inputFiles.value]))
                raise RuntimeError(error)

            if not os.path.exists(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            for iFile, oFile in outFiles.items():
                if os.path.isdir(iFile):  # If the input is a directory, copy the directory's content
                    chunk.logger.info('Publish directory {} into {}'.format(iFile, oFile))
                    du.copy_tree(iFile, oFile)
                else:
                    chunk.logger.info('Publish file {} into {}'.format(iFile, oFile))
                    shutil.copyfile(iFile, oFile)
            chunk.logger.info('Publish end')
        finally:
            chunk.logManager.end()
