__version__ = "4.1"

import json
import os
from collections import Counter

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


class LdrToHdrMerge(desc.AVCommandLineNode):
    commandLine = 'aliceVision_LdrToHdrMerge {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=2)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Panorama HDR'
    documentation = '''
Merge LDR images into HDR images.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="response",
            label="Response File",
            description="Response file.",
            value="",
            uid=[0],
        ),
        desc.IntParam(
            name="userNbBrackets",
            label="Number Of Brackets",
            description="Number of exposure brackets per HDR image (0 for automatic detection).",
            value=0,
            range=(0, 15, 1),
            uid=[],
            group="user",  # not used directly on the command line
        ),
        desc.IntParam(
            name="nbBrackets",
            label="Automatic Nb Brackets",
            description="Number of exposure brackets used per HDR image.\n"
                        "It is detected automatically from input Viewpoints metadata if 'userNbBrackets'\n"
                        "is 0, else it is equal to 'userNbBrackets'.",
            value=0,
            range=(0, 10, 1),
            uid=[0],
            group="bracketsParams"
        ),
        desc.BoolParam(
            name="offsetRefBracketIndexEnabled",
            label="Manually Specify Ref Bracket",
            description="Manually specify the reference bracket index to control the exposure of the HDR image.",
            value=False,
            uid=[0],
            group="user",  # not used directly on the command line
        ),
        desc.IntParam(
            name="offsetRefBracketIndex",
            label="Offset Ref Bracket Index",
            description="0 to use the center bracket.\n"
                        "+N to use a more exposed bracket or -N to use a less exposed bracket.",
            value=1,
            range=(-4, 4, 1),
            uid=[0],
            enabled= lambda node: (node.nbBrackets.value != 1 and node.offsetRefBracketIndexEnabled.value),
        ),
        desc.FloatParam(
            name="meanTargetedLumaForMerging",
            label="Targeted Luminance For Merging",
            description="Expected mean luminance of the HDR images used to compute the final panorama.",
            value=0.4,
            range=(0.0, 1.0, 0.01),
            uid=[0],
            enabled= lambda node: (node.nbBrackets.value != 1 and not node.offsetRefBracketIndexEnabled.value),
        ),
        desc.FloatParam(
            name='minSignificantValue',
            label='Minimum Significant Value',
            description='Minimum channel input value to be considered in advanced pixelwise merging.',
            value=0.05,
            range=(0.0, 1.0, 0.001),
            uid=[0],
            enabled= lambda node: (node.nbBrackets.value != 1),
        ),
        desc.FloatParam(
            name='maxSignificantValue',
            label='Maximum Significant Value',
            description='Maximum channel input value to be considered in advanced pixelwise merging.',
            value=0.995,
            range=(0.0, 1.0, 0.001),
            uid=[0],
            enabled= lambda node: (node.nbBrackets.value != 1),
        ),
        desc.BoolParam(
            name='computeLightMasks',
            label='Compute Light Masks',
            description="Compute masks of low and high lights and missing info.",
            value=False,
            uid=[0],
            enabled= lambda node: node.nbBrackets.value != 1,
        ),
        desc.BoolParam(
            name="byPass",
            label="Bypass",
            description="Bypass HDR creation and use the medium bracket as the source for the next steps.",
            value=False,
            uid=[0],
            enabled= lambda node: node.nbBrackets.value != 1,
        ),
        desc.BoolParam(
            name="keepSourceImageName",
            label="Keep Source Image Name",
            description="Keep the filename of the input image selected as central image for the output image filename.",
            value=False,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="fusionWeight",
            label="Fusion Weight",
            description="Weight function used to fuse all LDR images together:\n"
                        " - gaussian\n"
                        " - triangle\n"
                        " - plateau",
            value="gaussian",
            values=["gaussian", "triangle", "plateau"],
            exclusive=True,
            uid=[0],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name="channelQuantizationPower",
            label="Channel Quantization Power",
            description="Quantization level like 8 bits or 10 bits.",
            value=10,
            range=(8, 14, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.ChoiceParam(
            name="workingColorSpace",
            label="Working Color Space",
            description="Allows you to choose the color space in which the data are processed.",
            value="sRGB",
            values=["sRGB", "Linear", "ACES2065-1", "ACEScg", "no_conversion"],
            exclusive=True,
            uid=[0],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.BoolParam(
            name="enableHighlight",
            label="Enable Highlight",
            description="Enable highlights correction.",
            value=False,
            uid=[0],
            group="user",  # not used directly on the command line
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.FloatParam(
            name="highlightCorrectionFactor",
            label="Highlights Correction",
            description="Pixels saturated in all input images have a partial information about their real luminance.\n"
                        "We only know that the value should be >= to the standard HDRfusion.\n"
                        "This parameter allows to perform a post-processing step to put saturated pixels to a constant\n"
                        "value defined by the `highlightsMaxLuminance` parameter.\n"
                        "This parameter is float to enable to weight this correction.",
            value=1.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
            enabled= lambda node: node.enableHighlight.enabled and node.enableHighlight.value,
        ),
        desc.FloatParam(
            name="highlightTargetLux",
            label="Highlight Target Luminance (Lux)",
            description="This is an arbitrary target value (in Lux) used to replace the unknown luminance value of the saturated pixels.\n"
                        "\n"
                        "Some Outdoor Reference Light Levels:\n"
                        " - 120,000 lux: Brightest sunlight\n"
                        " - 110,000 lux: Bright sunlight\n"
                        " - 20,000 lux: Shade illuminated by entire clear blue sky, midday\n"
                        " - 1,000 lux: Typical overcast day, midday\n"
                        " - 400 lux: Sunrise or sunset on a clear day\n"
                        " - 40 lux: Fully overcast, sunset/sunrise\n"
                        "\n"
                        "Some Indoor Reference Light Levels:\n"
                        " - 20000 lux: Max Usually Used Indoor\n"
                        " - 750 lux: Supermarkets\n"
                        " - 500 lux: Office Work\n"
                        " - 150 lux: Home\n",
            value=120000.0,
            range=(1000.0, 150000.0, 1.0),
            uid=[0],
            enabled= lambda node: node.enableHighlight.enabled and node.enableHighlight.value and node.highlightCorrectionFactor.value != 0,
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="Storage Data Type",
            description="Storage image data type:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            value="float",
            values=["float", "half", "halfFinite", "auto"],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name="outputFolder",
            label="Folder",
            description="Path to the folder containing the merged HDR images.",
            value=desc.Node.internalFolder,
            uid=[],
            group="",  # do not export on the command line
        ),
        desc.File(
            name="outSfMData",
            label="SfMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
            uid=[],
        )
    ]

    @classmethod
    def update(cls, node):
        if not isinstance(node.nodeDesc, cls):
            raise ValueError("Node {} is not an instance of type {}".format(node, cls))
        # TODO: use Node version for this test
        if "userNbBrackets" not in node.getAttributes().keys():
            # Old version of the node
            return
        if node.userNbBrackets.value != 0:
            node.nbBrackets.value = node.userNbBrackets.value
            return
        cameraInitOutput = node.input.getLinkParam(recursive=True)
        if not cameraInitOutput:
            node.nbBrackets.value = 0
            return
        if not cameraInitOutput.node.hasAttribute("viewpoints"):
            if cameraInitOutput.node.hasAttribute("input"):
                cameraInitOutput = cameraInitOutput.node.input.getLinkParam(recursive=True)
        if cameraInitOutput and cameraInitOutput.node and cameraInitOutput.node.hasAttribute("viewpoints"):
            viewpoints = cameraInitOutput.node.viewpoints.value
        else:
            # No connected CameraInit
            node.nbBrackets.value = 0
            return

        inputs = []
        for viewpoint in viewpoints:
            jsonMetadata = viewpoint.metadata.value
            if not jsonMetadata:
                # no metadata, we cannot find the number of brackets
                node.nbBrackets.value = 0
                return
            d = json.loads(jsonMetadata)
            fnumber = findMetadata(d, ["FNumber", "Exif:ApertureValue", "ApertureValue", "Aperture"], "")
            shutterSpeed = findMetadata(d, ["ExposureTime", "Shutter Speed Value", "ShutterSpeedValue", "ShutterSpeed"], "")
            iso = findMetadata(d, ["Exif:ISOSpeedRatings", "ISOSpeedRatings", "ISO"], "")
            if not fnumber and not shutterSpeed:
                # If one image without shutter or fnumber, we cannot found the number of brackets.
                # We assume that there is no multi-bracketing, so nothing to do.
                node.nbBrackets.value = 1
                return
            inputs.append((viewpoint.path.value, (float(fnumber), float(shutterSpeed), float(iso))))
        inputs.sort()

        exposureGroups = []
        exposures = []
        prevFnumber = 0.0
        prevShutterSpeed = 0.0
        prevIso = 0.0
        prevPath = None  # Stores the dirname of the previous parsed image
        newGroup = False  # True if a new exposure group needs to be created (useful when there are several datasets)
        for path, exp in inputs:
            # If the dirname of the previous image and the dirname of the current image do not match, this means that the
            # dataset that is being parsed has changed. A new group needs to be created but will fail to be detected in the
            # next "if" statement if the new dataset's exposure levels are different. Setting "newGroup" to True prevents this
            # from happening.
            if prevPath is not None and prevPath != os.path.dirname(path):
                newGroup = True

            # A new group is created if the current image's exposure level is larger than the previous image's, if there
            # were any changes in the ISO or aperture value, or if a new dataset has been detected with the path.
            # Since the input images are ordered, the shutter speed should always be decreasing, so a shutter speed larger
            # than the previous one indicates the start of a new exposure group.
            fnumber, shutterSpeed, iso = exp
            if exposures:
                prevFnumber, prevShutterSpeed, prevIso = exposures[-1]
            if exposures and len(exposures) >= 1 and (fnumber != prevFnumber or shutterSpeed < prevShutterSpeed or iso != prevIso) or newGroup:
                exposureGroups.append(exposures)
                exposures = [exp]
            else:
                exposures.append(exp)

            prevPath = os.path.dirname(path)
            newGroup = False

        exposureGroups.append(exposures)

        exposures = None
        bracketSizes = Counter()
        if len(exposureGroups) == 1:
            if len(set(exposureGroups[0])) == 1:
                # Single exposure and multiple views
                node.nbBrackets.value = 1
            else:
                # Single view and multiple exposures
                node.nbBrackets.value = len(exposureGroups[0])
        else:
            for expGroup in exposureGroups:
                bracketSizes[len(expGroup)] += 1

            if len(bracketSizes) == 0:
                node.nbBrackets.value = 0
            else:
                bestTuple = None
                for tuple in bracketSizes.most_common():
                    if bestTuple is None or tuple[1] > bestTuple[1]:
                        bestTuple = tuple
                    elif tuple[1] == bestTuple[1]:
                        bestTuple = tuple if tuple[0] > bestTuple[0] else bestTuple

                bestBracketSize = bestTuple[0]
                node.nbBrackets.value = bestBracketSize

    def processChunk(self, chunk):
        # Trick to avoid sending --nbBrackets to the command line when the bracket detection is automatic.
        # Otherwise, the AliceVision executable has no way of determining whether the bracket detection was automatic
        # or if it was hard-set by the user.
        self.commandLine = "aliceVision_LdrToHdrMerge {allParams}"
        if chunk.node.userNbBrackets.value == chunk.node.nbBrackets.value:
            self.commandLine += "{bracketsParams}"
        super(LdrToHdrMerge, self).processChunk(chunk)
