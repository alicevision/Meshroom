from __future__ import print_function

__version__ = "0.1"

from meshroom.core import desc
import shutil
import glob
import os
import json

class PublishToBaseDir(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')

    category = 'Export'
    documentation = '''
This node copies the results to the /mnt/models/<project name>_XXX directory. It also saves a copy
of the current pipeline as src.mg.
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
            label="Base Output Folder",
            description="",
            value="/mnt/models",
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

    def get_output_directory(self, prjname, base_dir):
        cnt = 0
        path = os.path.join(base_dir, prjname)

        while os.path.isdir(path):
            path = os.path.join(base_dir,"{}_{}".format(prjname, "%03d"%cnt))
            cnt += 1

        return path

    def processChunk(self, chunk):
        try:
            if not chunk.node.output.value:
                chunk.logger.warning('No Base Output Folder')
                return

            graph = chunk.node._attributes.parent().parent().parent()
            prjname = graph.name

            output_dir = self.get_output_directory(prjname, chunk.node.output.value)
            chunk.logManager.start(chunk.node.verboseLevel.value)

            chunk.logger.info('Output Directory: {}'.format(output_dir))

            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            #
            # The .mg format was taken from:
            #   https://github.com/alicevision/meshroom/blob/18be350e6f7a410941d2d609722b9459469ea2a2/meshroom/core/graph.py#L1008-L1014
            #
            data = {
                graph.IO.Keys.Header: graph.header,
                graph.IO.Keys.Graph: graph.toDict(),
            }

            with open(os.path.join(output_dir, "src.mg"), 'w') as jsonFile:
                json.dump(data, jsonFile, indent=4)

            if not chunk.node.inputFiles:
                chunk.logger.warning('Nothing to publish')
                return

            outFiles = self.resolvedPaths(chunk.node.inputFiles.value, output_dir)

            if not outFiles:
                error = 'Publish: input files listed, but nothing to publish'
                chunk.logger.error(error)
                chunk.logger.info('Listed input files: {}'.format([i.value for i in chunk.node.inputFiles.value]))
                raise RuntimeError(error)

            for iFile, oFile in outFiles.items():
                chunk.logger.info('Publish file {} into {}'.format(iFile, oFile))
                shutil.copyfile(iFile, oFile)
            chunk.logger.info('Publish end')
        finally:
            chunk.logManager.end()
