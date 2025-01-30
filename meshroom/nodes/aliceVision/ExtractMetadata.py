__version__ = "0.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import distutils.dir_util as du
import shutil
import glob
import os


class ExtractMetadata(desc.Node):
    size = desc.DynamicNodeSize("input")

    category = 'Utils'
    documentation = '''
Using exifTool, this node extracts metadata of all images referenced in a sfmData and store them in appropriate files.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file input.",
            value="",
        ),
        desc.BoolParam(
            name="keepFilename",
            label="Keep Filename",
            description="Keep the filename of the inputs for the outputs.",
            value=False,
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Metadata file extension.",
            value="txt",
            values=["txt", "xml", "xmp"],
            exclusive=True,
        ),
        desc.StringParam(
            name="arguments",
            label="Arguments",
            description="ExifTool command arguments",
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

    outputs = [
        desc.File(
            name="output",
            label="Result Folder",
            description="Output path for the resulting images.",
            value=desc.Node.internalFolder,
        ),
    ]

    def resolvedPaths(self, inputSfm, outDir, keepFilename, extension):
        import pyalicevision as av
        from pathlib import Path

        paths = {}
        dataAV = av.sfmData.SfMData()
        if av.sfmDataIO.load(dataAV, inputSfm, av.sfmDataIO.ALL) and os.path.isdir(outDir):
            views = dataAV.getViews()
            for id, v in views.items():
                inputFile = v.getImage().getImagePath()
                if keepFilename:
                    outputMetadata = os.path.join(outDir, Path(inputFile).stem + "." + extension)
                else:
                    outputMetadata = os.path.join(outDir, str(id) + "." + extension)
                paths[inputFile] = outputMetadata

        return paths

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            
            if not chunk.node.input:
                chunk.logger.warning('No image file to process')
                return

            outFiles = self.resolvedPaths(chunk.node.input.value, chunk.node.output.value, chunk.node.keepFilename.value, chunk.node.extension.value)

            if not outFiles:
                error = 'ExtractMetadata: No input files! Check that a sfmData is connected as input.'
                chunk.logger.error(error)
                raise RuntimeError(error)

            if not os.path.exists(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            for iFile, oFile in outFiles.items():
                if chunk.node.extension.value == 'txt':
                    cmd = 'exiftool ' + chunk.node.arguments.value.strip() + ' ' + iFile + ' > ' + oFile
                elif chunk.node.extension.value == 'xml':
                    cmd = 'exiftool -X ' + chunk.node.arguments.value.strip() + ' ' + iFile + ' > ' + oFile
                else: #xmp
                    cmd = 'exiftool -tagsfromfile ' + iFile + ' ' + chunk.node.arguments.value.strip() + ' ' + oFile
                chunk.logger.debug(cmd)
                try:
                    os.system(cmd)
                except:
                    chunk.logger.error("exifTool command failed ! Check that exifTool can be accessed on your system.")
                    raise RuntimeError(error)
                if not os.path.exists(oFile):
                    info = 'No metadata extracted for file ' + iFile
                    chunk.logger.info(info)
            chunk.logger.info('Metadata extraction end')
            
        finally:
            chunk.logManager.end()
