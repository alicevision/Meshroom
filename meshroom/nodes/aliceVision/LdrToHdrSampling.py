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


class DividedInputNodeSize(desc.DynamicNodeSize):
    '''
    The LDR2HDR will reduce the amount of views in the SfMData.
    This class converts the number of LDR input views into the number of HDR output views.
    '''
    def __init__(self, param, divParam):
        super(DividedInputNodeSize, self).__init__(param)
        self._divParam = divParam
    def computeSize(self, node):
        s = super(DividedInputNodeSize, self).computeSize(node)
        divParam = node.attribute(self._divParam)
        if divParam.value == 0:
            return s
        return s / divParam.value


class LdrToHdrSampling(desc.CommandLineNode):
    commandLine = 'aliceVision_LdrToHdrSampling {allParams}'
    size = DividedInputNodeSize('input', 'nbBrackets')
    parallelization = desc.Parallelization(blockSize=2)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Panorama HDR'
    documentation = '''
    Sample pixels from Low range images for HDR creation
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
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
        desc.BoolParam(
            name='byPass',
            label='Bypass',
            description="Bypass HDR creation and use the medium bracket as the source for the next steps",
            value=False,
            uid=[0],
            group='internal',
            enabled= lambda node: node.nbBrackets.value != 1,
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
        desc.IntParam(
            name='blockSize',
            label='Block Size',
            description='Size of the image tile to extract a sample.',
            value=256,
            range=(8, 1024, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name='radius',
            label='Patch Radius',
            description='Radius of the patch used to analyze the sample statistics.',
            value=5,
            range=(0, 10, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name='maxCountSample',
            label='Max Number of Samples',
            description='Max number of samples per image group.',
            value=200,
            range=(10, 1000, 10),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.BoolParam(
            name='debug',
            label='Export Debug Files',
            description="Export debug files to analyze the sampling strategy.",
            value=False,
            uid=[],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
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
            name='output',
            label='Output Folder',
            description='Output path for the samples.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

    def processChunk(self, chunk):
        if chunk.node.nbBrackets.value == 1 or chunk.node.byPass.value:
            return
        super(LdrToHdrSampling, self).processChunk(chunk)

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

