__version__ = "2.0"

import json
import os

from meshroom.core import desc

def findMetadata(d, keys, defaultValue):
    v = None
    for key in keys:
        v = d.get(key, None)
        k = key.lower()
        if v != None:
            return v
        for dk, dv in d.iteritems():
            dkm = dk.lower().replace(" ", "")
            if dkm == key.lower():
                return dv
            dkm = dkm.split(":")[-1]
            dkm = dkm.split("/")[-1]
            if dkm == k:
                return dv
    return defaultValue



class LdrToHdrCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_LdrToHdrCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    documentation = '''
    Calibrate LDR to HDR response curve from samples
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='samples',
            label='Samples folder',
            description='Samples folder',
            value=desc.Node.internalFolder,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='calibrationMethod',
            label='Calibration Method',
            description="Method used for camera calibration \n"
                        " * Linear: Disable the calibration and assumes a linear Camera Response Function. If images are encoded in a known colorspace (like sRGB for JPEG), the images will be automatically converted to linear. \n"
                        " * Debevec: This is the standard method for HDR calibration. \n"
                        " * Grossberg: Based on learned database of cameras, it allows to reduce the CRF to few parameters while keeping all the precision. \n"
                        " * Laguerre: Simple but robust method estimating the minimal number of parameters. \n"
                        " * Robertson: First method for HDR calibration in the literature. \n",
            values=['linear', 'debevec', 'grossberg', 'laguerre'],
            value='debevec',
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='calibrationWeight',
            label='Calibration Weight',
            description="Weight function used to calibrate camera response \n"
                        " * default (automatically selected according to the calibrationMethod) \n"
                        " * gaussian \n"
                        " * triangle \n"
                        " * plateau",
            value='default',
            values=['default', 'gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='userNbBrackets',
            label='Number of Brackets',
            description='Number of exposure brackets per HDR image (0 for automatic detection).',
            value=0,
            range=(0, 15, 1),
            uid=[0],
            group='user',  # not used directly on the command line
        ),
        desc.IntParam(
            name='nbBrackets',
            label='Automatic Nb Brackets',
            description='Number of exposure brackets used per HDR image. It is detected automatically from input Viewpoints metadata if "userNbBrackets" is 0, else it is equal to "userNbBrackets".',
            value=0,
            range=(0, 10, 1),
            uid=[],
        ),
        desc.BoolParam(
            name='byPass',
            label='bypass convert',
            description="Bypass HDR creation and use the medium bracket as the source for the next steps",
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='channelQuantizationPower',
            label='Channel Quantization Power',
            description='Quantization level like 8 bits or 10 bits.',
            value=10,
            range=(8, 14, 1),
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
       desc.File(
            name='response',
            label='Output response  File',
            description='Path to the output response file',
            value=desc.Node.internalFolder + 'response.csv',
            uid=[],
        )
    ]

    @classmethod
    def update(cls, node):
        if not isinstance(node.nodeDesc, cls):
            raise ValueError("Node {} is not an instance of type {}".format(node, cls))
        # TODO: use Node version for this test
        if 'userNbBrackets' not in node.getAttributes().keys():
            # Old version of the node
            return
        if node.userNbBrackets.value != 0:
            node.nbBrackets.value = node.userNbBrackets.value
            return
        # logging.info("[LDRToHDR] Update start: version:" + str(node.packageVersion))
        cameraInitOutput = node.input.getLinkParam(recursive=True)
        if not cameraInitOutput:
            node.nbBrackets.value = 0
            return
        print("LdrToHdrCalib cameraInitOutput: " + str(cameraInitOutput))
        viewpoints = cameraInitOutput.node.viewpoints.value
        print("LdrToHdrCalib viewpoints: " + str(viewpoints))

        # logging.info("[LDRToHDR] Update start: nb viewpoints:" + str(len(viewpoints)))
        inputs = []
        for viewpoint in viewpoints:
            jsonMetadata = viewpoint.metadata.value
            if not jsonMetadata:
                # no metadata, we cannot found the number of brackets
                node.nbBrackets.value = 0
                return
            d = json.loads(jsonMetadata)
            fnumber = findMetadata(d, ["FNumber", "Exif:ApertureValue", "ApertureValue", "Aperture"], "")
            shutterSpeed = findMetadata(d, ["Exif:ShutterSpeedValue", "ShutterSpeedValue", "ShutterSpeed"], "")
            iso = findMetadata(d, ["Exif:ISOSpeedRatings", "ISOSpeedRatings", "ISO"], "")
            if not fnumber and not shutterSpeed:
                # If one image without shutter or fnumber, we cannot found the number of brackets.
                # We assume that there is no multi-bracketing, so nothing to do.
                node.nbBrackets.value = 1
                return
            inputs.append((viewpoint.path.value, (fnumber, shutterSpeed, iso)))
        inputs.sort()

        exposureGroups = []
        exposures = []
        for path, exp in inputs:
            if exposures and exp != exposures[-1] and exp == exposures[0]:
                exposureGroups.append(exposures)
                exposures = [exp]
            else:
                exposures.append(exp)
        exposureGroups.append(exposures)
        exposures = None
        bracketSizes = set()
        if len(exposureGroups) == 1:
            node.nbBrackets.value = 1
        else:
            for expGroup in exposureGroups:
                bracketSizes.add(len(expGroup))
            if len(bracketSizes) == 1:
                node.nbBrackets.value = bracketSizes.pop()
                # logging.info("[LDRToHDR] nb bracket size:" + str(node.nbBrackets.value))
            else:
                node.nbBrackets.value = 0
        # logging.info("[LDRToHDR] Update end")

