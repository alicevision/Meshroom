from __future__ import print_function

__version__ = "1.3"

from meshroom.core import desc
import distutils.dir_util as du
import shutil
#import glob
import os

import pyalicevision as av
import json
from pathlib import Path

from segmentationRDS import image, segmentation

import torch


class ImageSegmentationRDS(desc.Node):
    size = desc.DynamicNodeSize('input')
    gpu = desc.Level.INTENSIVE
    parallelization = desc.Parallelization(blockSize=50)

    category = 'Utils'
    documentation = '''
Generate a binary mask corresponding to the input text prompt.
First a recognition model (image to tags) is launched on the input image.
If the prompt or a synonym is detected in the returned list of tags the detection model (tag to bounded box) is launched.
Detection can be forced by setting to True the appropriate parameter.
If at least one bounded box is returned the segmentation model (bounded box to binary mask) is launched.
Bounded box sizes can be increased by a ratio from 0 to 100%
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file input.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="recognitionModelPath",
            label="Recognition Model",
            description="Weights file for the recognition model.",
            value=os.getenv('RECOGNITION_MODEL_PATH'),
            uid=[0],
        ),
        desc.File(
            name="detectionModelPath",
            label="Detection Model",
            description="Weights file for the detection model.",
            value=os.getenv('DETECTION_MODEL_PATH'),
            uid=[0],
        ),
        desc.File(
            name="detectionConfigPath",
            label="Detection Config",
            description="Config file for the detection model.",
            value=os.getenv('DETECTION_CONFIG_PATH'),
            uid=[0],
        ),
        desc.File(
            name="segmentationModelPath",
            label="Segmentation Model",
            description="Weights file for the segmentation model.",
            value=os.getenv('SEGMENTATION_MODEL_PATH'),
            uid=[0],
        ),
        desc.StringParam(
            name="prompt",
            label="Prompt",
            description="What to segment, separated by point or one item per line",
            value="person",
            semantic="multiline",
            uid=[0],
        ),
        desc.StringParam(
            name="synonyms",
            label="Synonyms",
            description="Synonyms to prompt separated by commas or one item per line. eg: man,woman,boy,girl,human,people can be used as synonyms of person",
            value="man\nwoman\nboy\ngirl\nhuman\npeople",
            semantic="multiline",
            uid=[0],
        ),
        desc.BoolParam(
            name="forceDetection",
            label="Force Detection",
            description="Launch detection step even if nor the prompt neither any synonyms are recognized",
            value=False,
            uid=[0],
        ),
        desc.IntParam(
            name="bboxMargin",
            label="Detection Margin",
            description="Increase bounded box dimensions by the selected percentage",
            range=(0,100,1),
            value=0,
            uid=[0],
        ),
        desc.BoolParam(
            name="maskInvert",
            label="Invert Masks",
            description="Invert mask values. If selected, the pixels corresponding to the mask will be set to 0 instead of 255.",
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name="useGpu",
            label="Use GPU",
            description="Use GPU for computation if available",
            value=True,
            uid=[],
        ),
        desc.BoolParam(
            name="keepFilename",
            label="Keep Filename",
            description="Keep Input Filename",
            value=False,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Output image file extension.\n"
                        "If unset, the output file extension will match the input's if possible.",
            value="exr",
            values=["exr", "png", "jpg"],
            exclusive=True,
            uid=[0],
            group='', # remove from command line params
        ),
        desc.BoolParam(
            name="outputBboxImage",
            label="Output Bounded Box Image",
            description="Write source image with bounded boxes baked in.",
            value=False,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug"],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="Masks Folder",
            description="Output path for the masks.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name="masks",
            label="Masks",
            description="Generated segmentation masks.",
            semantic="image",
            value=lambda attr: desc.Node.internalFolder + ("<FILENAME>" if attr.node.keepFilename.value else "<VIEW_ID>") + "." + attr.node.extension.value,
            group="",
            uid=[],
        ),
    ]

    def resolvedPaths(self, inputSfm, outDir, keepFilename, ext):
        paths = {}
        dataAV = av.sfmData.SfMData()
        if av.sfmDataIO.load(dataAV, inputSfm, av.sfmDataIO.ALL) and os.path.isdir(outDir):
            views = dataAV.getViews()
            for id, v in views.items():
                inputFile = v.getImage().getImagePath()
                if keepFilename:
                    outputFileMask = os.path.join(outDir, Path(inputFile).stem + '.' + ext)
                    outputFileBoxes = os.path.join(outDir, Path(inputFile).stem + "_bboxes" + '.jpg')
                else:
                    outputFileMask = os.path.join(outDir, str(id) + '.' + ext)
                    outputFileBoxes = os.path.join(outDir, str(id) + "_bboxes" + '.jpg')
                paths[inputFile] = (outputFileMask, outputFileBoxes)

        return paths

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)

            if not chunk.node.input:
                chunk.logger.warning('Nothing to segment')
                return
            if not chunk.node.output.value:
                return

            chunk.logger.info('Chunk range from {} to {}'.format(chunk.range.start, chunk.range.last))

            outFiles = self.resolvedPaths(chunk.node.input.value, chunk.node.output.value, chunk.node.keepFilename.value, chunk.node.extension.value)

            if not os.path.exists(chunk.node.output.value):
                os.mkdir(chunk.node.output.value)

            os.environ['TOKENIZERS_PARALLELISM'] = 'true' # required to avoid warning on tokenizers

            processor = segmentation.segmentationRDS(RAM_CHECKPOINT_PATH = chunk.node.recognitionModelPath.value,
                                                     GD_CONFIG_PATH = chunk.node.detectionConfigPath.value,
                                                     GD_CHECKPOINT_PATH = chunk.node.detectionModelPath.value,
                                                     SAM_CHECKPOINT_PATH = chunk.node.segmentationModelPath.value,
                                                     useGPU = chunk.node.useGpu.value)

            prompt = chunk.node.prompt.value.replace('\n','.')
            chunk.logger.debug('prompt: {}'.format(prompt))
            synonyms = chunk.node.synonyms.value.replace('\n',',')
            chunk.logger.debug('synonyms: {}'.format(synonyms))

            for k, (iFile, oFile) in enumerate(outFiles.items()):
                if k >= chunk.range.start and k <= chunk.range.last:
                    img = image.loadImage(iFile)
                    mask, bboxes, tags = processor.process(image = img,
                                                           prompt = chunk.node.prompt.value,
                                                           synonyms = chunk.node.synonyms.value,
                                                           force = chunk.node.forceDetection.value,
                                                           bboxMargin = chunk.node.bboxMargin.value,
                                                           invert = chunk.node.maskInvert.value,
                                                           verbose = False)

                    chunk.logger.debug('image: {}'.format(iFile))
                    chunk.logger.debug('tags: {}'.format(tags))
                    chunk.logger.debug('bboxes: {}'.format(bboxes))

                    image.writeImage(oFile[0], mask)

                    if (chunk.node.outputBboxImage.value):
                        imgBoxes = (img * 255.0).astype('uint8')
                        for bbox in bboxes:
                            imgBoxes = image.addRectangle(imgBoxes, bbox)
                        image.writeImage(oFile[1], imgBoxes)

            del processor
            torch.cuda.empty_cache()

        finally:
            chunk.logManager.end()

    def stopProcess(sel, chunk):
        try:
            del processor
        except:
            pass

