__version__ = "4.0"

import json

from meshroom.core import desc

def findMetadata(d, keys, defaultValue):
    v = None
    for key in keys:
        v = d.get(key, None)
        k = key.lower()
        if v is not None:
            return v
        for dk, dv in d.items():
            dkm = dk.lower().replace(" ", "")
            if dkm == key.lower():
                return dv
            dkm = dkm.split(":")[-1]
            dkm = dkm.split("/")[-1]
            if dkm == k:
                return dv
    return defaultValue


class LdrToHdrMerge(desc.CommandLineNode):
    commandLine = 'aliceVision_LdrToHdrMerge {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=2)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Panorama HDR'
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
            name='response',
            label='Response file',
            description='Response file',
            value='',
            uid=[0],
        ),
        desc.IntParam(
            name='userNbBrackets',
            label='Number of Brackets',
            description='Number of exposure brackets per HDR image (0 for automatic detection).',
            value=0,
            range=(0, 15, 1),
            uid=[],
            group='user',  # not used directly on the command line
        ),
        desc.IntParam(
            name='nbBrackets',
            label='Automatic Nb Brackets',
            description='Number of exposure brackets used per HDR image. It is detected automatically from input Viewpoints metadata if "userNbBrackets" is 0, else it is equal to "userNbBrackets".',
            value=0,
            range=(0, 10, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='offsetRefBracketIndex',
            label='Offset Ref Bracket Index',
            description='Zero to use the center bracket. +N to use a more exposed bracket or -N to use a less exposed backet.',
            value=1,
            range=(-4, 4, 1),
            uid=[0],
            enabled= lambda node: node.nbBrackets.value != 1,
        ),
        desc.BoolParam(
            name='byPass',
            label='Bypass',
            description="Bypass HDR creation and use the medium bracket as the source for the next steps.",
            value=False,
            uid=[0],
            enabled= lambda node: node.nbBrackets.value != 1,
        ),
        desc.ChoiceParam(
            name='fusionWeight',
            label='Fusion Weight',
            description="Weight function used to fuse all LDR images together:\n"
                        " * gaussian \n"
                        " * triangle \n"
                        " * plateau",
            value='gaussian',
            values=['gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name='channelQuantizationPower',
            label='Channel Quantization Power',
            description='Quantization level like 8 bits or 10 bits.',
            value=10,
            range=(8, 14, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.BoolParam(
            name='enableHighlight',
            label='Enable Highlight',
            description="Enable highlights correction.",
            value=False,
            uid=[0],
            group='user',  # not used directly on the command line
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.FloatParam(
            name='highlightCorrectionFactor',
            label='Highlights Correction',
            description='Pixels saturated in all input images have a partial information about their real luminance.\n'
                        'We only know that the value should be >= to the standard hdr fusion.\n'
                        'This parameter allows to perform a post-processing step to put saturated pixels to a constant\n'
                        'value defined by the `highlightsMaxLuminance` parameter.\n'
                        'This parameter is float to enable to weight this correction.',
            value=1.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
            enabled= lambda node: node.enableHighlight.enabled and node.enableHighlight.value,
        ),
        desc.FloatParam(
            name='highlightTargetLux',
            label='Highlight Target Luminance (Lux)',
            description='This is an arbitrary target value (in Lux) used to replace the unknown luminance value of the saturated pixels.\n'
                        '\n'
                        'Some Outdoor Reference Light Levels:\n'
                        ' * 120,000 lux: Brightest sunlight\n'
                        ' * 110,000 lux: Bright sunlight\n'
                        ' * 20,000 lux: Shade illuminated by entire clear blue sky, midday\n'
                        ' * 1,000 lux: Typical overcast day, midday\n'
                        ' * 400 lux: Sunrise or sunset on a clear day\n'
                        ' * 40 lux: Fully overcast, sunset/sunrise\n'
                        '\n'
                        'Some Indoor Reference Light Levels:\n'
                        ' * 20000 lux: Max Usually Used Indoor\n'
                        ' * 750 lux: Supermarkets\n'
                        ' * 500 lux: Office Work\n'
                        ' * 150 lux: Home\n',
            value=120000.0,
            range=(1000.0, 150000.0, 1.0),
            uid=[0],
            enabled= lambda node: node.enableHighlight.enabled and node.enableHighlight.value and node.highlightCorrectionFactor.value != 0,
        ),
        desc.ChoiceParam(
            name='storageDataType',
            label='Storage Data Type',
            description='Storage image data type:\n'
                        ' * float: Use full floating point (32 bits per channel)\n'
                        ' * half: Use half float (16 bits per channel)\n'
                        ' * halfFinite: Use half float, but clamp values to avoid non-finite values\n'
                        ' * auto: Use half float if all values can fit, else use full float\n',
            value='float',
            values=['float', 'half', 'halfFinite', 'auto'],
            exclusive=True,
            uid=[0],
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
            name='outSfMData',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.sfm',
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
        if not cameraInitOutput.node.hasAttribute('viewpoints'):
            if cameraInitOutput.node.hasAttribute('input'):
                cameraInitOutput = cameraInitOutput.node.input.getLinkParam(recursive=True)
        if cameraInitOutput and cameraInitOutput.node and cameraInitOutput.node.hasAttribute('viewpoints'):
            viewpoints = cameraInitOutput.node.viewpoints.value
        else:
            # No connected CameraInit
            node.nbBrackets.value = 0
            return

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
            if len(set(exposureGroups[0])) == 1:
                # Single exposure and multiple views
                node.nbBrackets.value = 1
            else:
                # Single view and multiple exposures
                node.nbBrackets.value = len(exposureGroups[0])
        else:
            for expGroup in exposureGroups:
                bracketSizes.add(len(expGroup))
            if len(bracketSizes) == 1:
                node.nbBrackets.value = bracketSizes.pop()
                # logging.info("[LDRToHDR] nb bracket size:" + str(node.nbBrackets.value))
            else:
                node.nbBrackets.value = 0
        # logging.info("[LDRToHDR] Update end")

