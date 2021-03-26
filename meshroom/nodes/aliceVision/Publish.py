__version__ = "2.0"

import shutil
import glob
import os

from meshroom.core import desc


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
        desc.BoolParam(
            name='overwrite',
            label='Overwrite',
            description='Allow the overwriting of files.',
            value=False,
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
        paths = []
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                paths.append([f, os.path.join(outDir, os.path.basename(f))])
        return paths

    def processChunk(self, chunk):
        with desc.Logger(chunk) as logger:
            if not chunk.node.inputFiles:
                logger.warning('Nothing to publish')
                return
            if not chunk.node.output.value:
                logger.warning('No output folder set')
                return

            files = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

            if not files:
                logger.debug('Listed input files: {}'.format([i.value for i in chunk.node.inputFiles.value]))
                raise RuntimeError('Publish: input files listed, but nothing to publish')

            if not os.path.isdir(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            logger.makeProgressBar(len(files), 'Publish progress:')
            for index, file in enumerate(files):
                logger.info('Publish file {} into {}'.format(*file))
                if os.path.isfile(file[1]) and not chunk.node.overwrite.value:
                    logger.warning('File {} already exists, skipping'.format(file[1]))
                else:
                    shutil.copyfile(*file)
                logger.updateProgressBar(index+1)
            logger.info('Publish end')
