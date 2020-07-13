__version__ = "1.2"

import shutil
import glob
import os

from meshroom.core import desc


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
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (critical, error, warning, info, debug).''',
            value='info',
            values=['critical', 'error', 'warning', 'info', 'debug'],
            exclusive=True,
            uid=[],
            ),
        ]

    def resolvedPaths(self, inputFiles, outDir):
        paths = {}
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                paths[f] = os.path.join(outDir, os.path.basename(f))
        return paths

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            
            if not chunk.node.inputFiles:
                chunk.logger.warning('Nothing to publish')
                return
            if not chunk.node.output.value:
                chunk.logger.warning('No output folder set')
                return

            outFiles = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

            if not outFiles:
                chunk.logger.debug('Listed input files: {}'.format([i.value for i in chunk.node.inputFiles.value]))
                raise RuntimeError('Publish: input files listed, but nothing to publish')

            if not os.path.exists(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            for iFile, oFile in outFiles.items():
                chunk.logger.info('Publish file {} into {}'.format(iFile, oFile))
                shutil.copyfile(iFile, oFile)
            chunk.logger.info('Publish end')
        except Exception as e:
            chunk.logger.error(e)
            raise e
        finally:
            chunk.logManager.end()
