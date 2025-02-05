__version__ = "0.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL
from pathlib import Path

import pyalicevision as av

import distutils.dir_util as du
import shutil
import glob
import os
import subprocess


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
        desc.BoolParam(
            name="insertInSfm",
            label="Update sfmData",
            description="Insert the extracted metadata in the sfmData file.",
            value=False,
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
            description="Output path for the resulting metadata files.",
            value=desc.Node.internalFolder,
        ),
    ]

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            
            if chunk.node.input.value == "" or chunk.node.input.value[-4:].lower() != '.sfm':
                error = 'This node need to have a sfmData connected as input.'
                chunk.logger.error(error)
                raise RuntimeError(error)

            if not os.path.exists(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            dataAV = av.sfmData.SfMData()
            if av.sfmDataIO.load(dataAV, chunk.node.input.value, av.sfmDataIO.ALL):
                views = dataAV.getViews()
                for id, v in views.items():
                    inputFile = v.getImage().getImagePath()
                    chunk.logger.info(f"Processing {inputFile}")

                    if chunk.node.keepFilename.value:
                        outputMetadataFilename = os.path.join(chunk.node.output.value, Path(inputFile).stem + "." + chunk.node.extension.value)
                    else:
                        outputMetadataFilename = os.path.join(chunk.node.output.value, str(id) + "." + chunk.node.extension.value)

                    if chunk.node.extension.value == 'txt':
                        cmd = 'exiftool ' + chunk.node.arguments.value.strip() + ' ' + inputFile + ' > ' + outputMetadataFilename
                    elif chunk.node.extension.value == 'xml':
                        cmd = 'exiftool -X ' + chunk.node.arguments.value.strip() + ' ' + inputFile + ' > ' + outputMetadataFilename
                    else: #xmp
                        cmd = 'exiftool -tagsfromfile ' + inputFile + ' ' + chunk.node.arguments.value.strip() + ' ' + outputMetadataFilename

                    chunk.logger.debug(cmd)
                    error = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stderr.read().decode()

                    chunk.logger.debug(error)
                    
                    if error != "":
                        chunk.logger.error(error)
                        raise RuntimeError(error)
                    if not os.path.exists(outputMetadataFilename):
                        info = 'No metadata extracted for file ' + inputFile
                        chunk.logger.info(info)
                    elif chunk.node.insertInSfm.value:
                        cmd = 'exiftool ' + chunk.node.arguments.value.strip() + ' ' + inputFile
                        metadata = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode()
                        chunk.logger.debug(metadata)
                        lmeta = metadata.split('\n')
                        for i in range(1, len(lmeta)-1):
                            l = lmeta[i].split(':', 1)
                            v.getImageInfo().addMetadata('ExifTool:'+l[0].strip(), l[1].strip())

                if chunk.node.insertInSfm.value:
                    outputSfm = os.path.join(chunk.node.output.value, Path(chunk.node.input.value).stem + ".sfm")
                    av.sfmDataIO.save(dataAV, outputSfm, av.sfmDataIO.ALL)

                chunk.logger.info('Metadata extraction end')
            
        finally:
            chunk.logManager.end()
