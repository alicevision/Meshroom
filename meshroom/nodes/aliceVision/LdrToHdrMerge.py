__version__ = "4.1"

import json

from meshroom.core import desc
from meshroom.core.utils import COLORSPACES, EXR_STORAGE_DATA_TYPE, VERBOSE_LEVEL

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
        ),
        desc.File(
            name="response",
            label="Response File",
            description="Response file.",
            value="",
        ),
        desc.IntParam(
            name="userNbBrackets",
            label="Number Of Brackets",
            description="Number of exposure brackets per HDR image (0 for automatic detection).",
            value=0,
            range=(0, 15, 1),
            invalidate=False,
            group="user",  # not used directly on the command line
            errorMessage="The set number of brackets is not a multiple of the number of input images.\n"
                         "Errors will occur during the computation.",
            exposed=True,
        ),
        desc.IntParam(
            name="nbBrackets",
            label="Automatic Nb Brackets",
            description="Number of exposure brackets used per HDR image.\n"
                        "It is detected automatically from input Viewpoints metadata if 'userNbBrackets'\n"
                        "is 0, else it is equal to 'userNbBrackets'.",
            value=0,
            range=(0, 15, 1),
            group="bracketsParams",
        ),
        desc.BoolParam(
            name="offsetRefBracketIndexEnabled",
            label="Manually Specify Ref Bracket",
            description="Manually specify the reference bracket index to control the exposure of the HDR image.",
            value=False,
            group="user",  # not used directly on the command line
        ),
        desc.IntParam(
            name="offsetRefBracketIndex",
            label="Offset Ref Bracket Index",
            description="0 to use the center bracket.\n"
                        "+N to use a more exposed bracket or -N to use a less exposed bracket.",
            value=1,
            range=(-4, 4, 1),
            enabled=lambda node: (node.nbBrackets.value != 1 and node.offsetRefBracketIndexEnabled.value),
        ),
        desc.FloatParam(
            name="meanTargetedLumaForMerging",
            label="Targeted Luminance For Merging",
            description="Expected mean luminance of the HDR images used to compute the final panorama.",
            value=0.4,
            range=(0.0, 1.0, 0.01),
            enabled=lambda node: (node.nbBrackets.value != 1 and not node.offsetRefBracketIndexEnabled.value),
        ),
        desc.FloatParam(
            name="minSignificantValue",
            label="Minimum Significant Value",
            description="Minimum channel input value to be considered in advanced pixelwise merging.",
            value=0.05,
            range=(0.0, 1.0, 0.001),
            enabled=lambda node: (node.nbBrackets.value != 1),
        ),
        desc.FloatParam(
            name="maxSignificantValue",
            label="Maximum Significant Value",
            description="Maximum channel input value to be considered in advanced pixelwise merging.",
            value=0.995,
            range=(0.0, 1.0, 0.001),
            enabled=lambda node: (node.nbBrackets.value != 1),
        ),
        desc.BoolParam(
            name="computeLightMasks",
            label="Compute Light Masks",
            description="Compute masks of low and high lights and missing info.",
            value=False,
            enabled=lambda node: node.nbBrackets.value != 1,
        ),
        desc.BoolParam(
            name="byPass",
            label="Bypass",
            description="Bypass HDR creation and use the medium bracket as the source for the next steps.",
            value=False,
            enabled=lambda node: node.nbBrackets.value != 1,
            exposed=True,
        ),
        desc.BoolParam(
            name="keepSourceImageName",
            label="Keep Source Image Name",
            description="Keep the filename of the input image selected as central image for the output image filename.",
            value=False,
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
            enabled=lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name="channelQuantizationPower",
            label="Channel Quantization Power",
            description="Quantization level like 8 bits or 10 bits.",
            value=10,
            range=(8, 14, 1),
            advanced=True,
            enabled=lambda node: node.byPass.enabled and not node.byPass.value,
            exposed=True,
        ),
        desc.ChoiceParam(
            name="workingColorSpace",
            label="Working Color Space",
            description="Color space in which the data are processed.\n"
                        "If 'auto' is selected, the working color space will be 'Linear' if RAW images are detected; otherwise, it will be set to 'sRGB'.",
            values=COLORSPACES,
            value="AUTO",
            enabled=lambda node: node.byPass.enabled and not node.byPass.value,
            exposed=True,
        ),
        desc.BoolParam(
            name="enableHighlight",
            label="Enable Highlight",
            description="Enable highlights correction.",
            value=False,
            group="user",  # not used directly on the command line
            enabled=lambda node: node.byPass.enabled and not node.byPass.value,
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
            enabled=lambda node: node.enableHighlight.enabled and node.enableHighlight.value,
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
            enabled=lambda node: node.enableHighlight.enabled and node.enableHighlight.value and node.highlightCorrectionFactor.value != 0,
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="Storage Data Type",
            description="Storage image data type:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            values=EXR_STORAGE_DATA_TYPE,
            value="float",
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
            name="outputFolder",
            label="Folder",
            description="Path to the folder containing the merged HDR images.",
            value=desc.Node.internalFolder,
            group="",  # do not export on the command line
        ),
        desc.File(
            name="outSfMData",
            label="SfMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]

    @classmethod
    def update(cls, node):
        from pyalicevision import hdr as avhdr

        if not isinstance(node.nodeDesc, cls):
            raise ValueError("Node {} is not an instance of type {}".format(node, cls))
        # TODO: use Node version for this test
        if "userNbBrackets" not in node.getAttributes().keys():
            # Old version of the node
            return
        node.userNbBrackets.validValue = True  # Reset the status of "userNbBrackets"

        cameraInitOutput = node.input.getLinkParam(recursive=True)
        if not cameraInitOutput:
            node.nbBrackets.value = 0
            return
        if node.userNbBrackets.value != 0:
            # The number of brackets has been manually forced: check whether it is valid or not
            if cameraInitOutput and cameraInitOutput.node and cameraInitOutput.node.hasAttribute("viewpoints"):
                viewpoints = cameraInitOutput.node.viewpoints.value
                # The number of brackets should be a multiple of the number of input images
                if (len(viewpoints) % node.userNbBrackets.value != 0):
                    node.userNbBrackets.validValue = False
                else:
                    node.userNbBrackets.validValue = True
            node.nbBrackets.value = node.userNbBrackets.value
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

        inputs = avhdr.vectorli()
        for viewpoint in viewpoints:
            jsonMetadata = viewpoint.metadata.value
            if not jsonMetadata:
                # no metadata, we cannot find the number of brackets
                node.nbBrackets.value = 0
                return
            d = json.loads(jsonMetadata)

            # Find Fnumber
            fnumber = findMetadata(d, ["FNumber"], "")
            if fnumber == "":
                aperture = findMetadata(d, ["Exif:ApertureValue", "ApertureValue", "Aperture"], "")
                if aperture == "":
                    fnumber = -1.0
                else:
                    fnumber = pow(2.0, aperture / 2.0)

            # Get shutter speed and ISO
            shutterSpeed = findMetadata(d, ["ExposureTime", "Exif:ShutterSpeedValue", "ShutterSpeedValue", "ShutterSpeed"], -1.0)
            iso = findMetadata(d, ["Exif:PhotographicSensitivity", "PhotographicSensitivity", "Photographic Sensitivity", "ISO"], -1.0)

            if not fnumber and not shutterSpeed:
                # If one image without shutter or fnumber, we cannot found the number of brackets.
                # We assume that there is no multi-bracketing, so nothing to do.
                node.nbBrackets.value = 1
                return

            exposure = LdrToHdrMerge.getExposure((float(fnumber), float(shutterSpeed), float(iso)))

            obj = avhdr.LuminanceInfo(viewpoint.viewId.value,viewpoint.path.value, exposure)
            inputs.append(obj)

        obj = avhdr.estimateGroups(inputs)

        if len(obj) == 0:
            node.nbBrackets.value = 0
            return

        node.nbBrackets.value = len(obj[0])

    @staticmethod
    def getExposure(exp, refIso = 100.0, refFnumber = 1.0):
        from pyalicevision import sfmData as avsfmdata

        fnumber, shutterSpeed, iso = exp
        obj = avsfmdata.ExposureSetting(shutterSpeed, fnumber, iso)
        return obj.getExposure()

    def processChunk(self, chunk):
        # Trick to avoid sending --nbBrackets to the command line when the bracket detection is automatic.
        # Otherwise, the AliceVision executable has no way of determining whether the bracket detection was automatic
        # or if it was hard-set by the user.
        self.commandLine = "aliceVision_LdrToHdrMerge {allParams}"
        if chunk.node.userNbBrackets.value == chunk.node.nbBrackets.value:
            self.commandLine += "{bracketsParams}"
        super(LdrToHdrMerge, self).processChunk(chunk)
