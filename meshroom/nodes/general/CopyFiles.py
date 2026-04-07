__version__ = "1.3"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import shutil
import glob
import os


class CopyFiles(desc.Node):
    size = desc.DynamicNodeSize("inputFiles")

    category = "Export"
    documentation = """
This node allows to copy files into a specific folder.
"""

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input",
                description="File or folder to copy.",
                value="",
            ),
            name="inputFiles",
            label="Input Files",
            description="Input files or folders' content to copy.",
            exposed=True,
        ),
        desc.File(
            name="output",
            label="Output Folder",
            description="Folder to copy to.",
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
                    # Do not concatenate the input folder's name with the output's
                    paths[f] = outDir
                else:
                    paths[f] = os.path.join(outDir, os.path.basename(f))
        return paths

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)

            if not chunk.node.inputFiles:
                chunk.logger.warning("No file to copy.")
                return
            if not chunk.node.output.value:
                return

            outFiles = self.resolvedPaths(chunk.node.inputFiles.value, chunk.node.output.value)

            if not outFiles:
                error = "CopyFiles: input files listed, but nothing to copy."
                chunk.logger.error(error)
                chunk.logger.info(f"Listed input files: {[i.value for i in chunk.node.inputFiles.value]}.")
                raise RuntimeError(error)

            if not os.path.exists(chunk.node.output.value):
                os.makedirs(chunk.node.output.value)

            for iFile, oFile in outFiles.items():
                # If the input is a directory, copy the directory's content
                if os.path.isdir(iFile):
                    chunk.logger.info(f"CopyFiles directory {iFile} into {oFile}.")
                    shutil.copytree(iFile, oFile, dirs_exist_ok=True)
                else:
                    chunk.logger.info(f"CopyFiles file {iFile} into {oFile}.")
                    shutil.copyfile(iFile, oFile)
            chunk.logger.info("CopyFiles end.")
        finally:
            chunk.logManager.end()
