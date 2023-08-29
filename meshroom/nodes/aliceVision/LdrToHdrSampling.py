__version__ = "4.0"

import json
import math
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
        # s is the total number of inputs and may include outliers, that will not be used
        # during computations and should thus be excluded from the size computation
        return (s - node.outliersNb) / divParam.value


class LdrToHdrSampling(desc.AVCommandLineNode):
    commandLine = 'aliceVision_LdrToHdrSampling {allParams}'
    size = DividedInputNodeSize('input', 'nbBrackets')
    parallelization = desc.Parallelization(blockSize=2)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Panorama HDR'
    documentation = '''
Sample pixels from Low range images for HDR creation.
'''

    outliersNb = 0  # Number of detected outliers among the input images

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
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
            errorMessage="The set number of brackets is not a multiple of the number of input images.\n"
                         "Errors will occur during the computation."
        ),
        desc.IntParam(
            name="nbBrackets",
            label="Automatic Nb Brackets",
            description="Number of exposure brackets used per HDR image.\n"
                        "It is detected automatically from input Viewpoints metadata if 'userNbBrackets'\n"
                        "is 0, else it is equal to 'userNbBrackets'.",
            value=0,
            range=(0, 15, 1),
            uid=[0],
            group="bracketsParams"
        ),
        desc.BoolParam(
            name="byPass",
            label="Bypass",
            description="Bypass HDR creation and use the medium bracket as the source for the next steps.",
            value=False,
            uid=[0],
            enabled= lambda node: node.nbBrackets.value != 1,
        ),
        desc.ChoiceParam(
            name="calibrationMethod",
            label="Calibration Method",
            description="Method used for camera calibration:\n"
                        " - AUTO: If RAW images are detected then Linear behavior is selected else Debevec calibration method is enabled.\n"
                        " - Linear: Disable the calibration and assumes a linear Camera Response Function. If images are encoded in a known colorspace (like sRGB for JPEG), the images will be automatically converted to linear.\n"
                        " - Debevec: This is the standard method for HDR calibration.\n"
                        " - Grossberg: Based on learned database of cameras, it allows to reduce the CRF to few parameters while keeping all the precision.\n"
                        " - Laguerre: Simple but robust method estimating the minimal number of parameters.",
            values=["AUTO", "linear", "debevec", "grossberg", "laguerre"],
            value="AUTO",
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
            value="AUTO",
            values=["AUTO", "sRGB", "Linear", "ACES2065-1", "ACEScg", "no_conversion"],
            exclusive=True,
            uid=[0],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name="blockSize",
            label="Block Size",
            description="Size of the image tile to extract a sample.",
            value=256,
            range=(8, 1024, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name="radius",
            label="Patch Radius",
            description="Radius of the patch used to analyze the sample statistics.",
            value=5,
            range=(0, 10, 1),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.IntParam(
            name="maxCountSample",
            label="Max Number Of Samples",
            description="Maximum number of samples per image group.",
            value=200,
            range=(10, 1000, 10),
            uid=[0],
            advanced=True,
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
        ),
        desc.BoolParam(
            name="debug",
            label="Export Debug Files",
            description="Export debug files to analyze the sampling strategy.",
            value=False,
            uid=[],
            enabled= lambda node: node.byPass.enabled and not node.byPass.value,
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
            name="output",
            label="Folder",
            description="Output path for the samples.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

    def processChunk(self, chunk):
        if chunk.node.nbBrackets.value == 1:
            return
        # Trick to avoid sending --nbBrackets to the command line when the bracket detection is automatic.
        # Otherwise, the AliceVision executable has no way of determining whether the bracket detection was automatic
        # or if it was hard-set by the user.
        self.commandLine = "aliceVision_LdrToHdrSampling {allParams}"
        if chunk.node.userNbBrackets.value == chunk.node.nbBrackets.value:
            self.commandLine += "{bracketsParams}"
        super(LdrToHdrSampling, self).processChunk(chunk)

    @classmethod
    def update(cls, node):
        if not isinstance(node.nodeDesc, cls):
            raise ValueError("Node {} is not an instance of type {}".format(node, cls))
        # TODO: use Node version for this test
        if "userNbBrackets" not in node.getAttributes().keys():
            # Old version of the node
            return
        node.outliersNb = 0  # Reset the number of detected outliers
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

        inputs = []
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
            inputs.append((viewpoint.path.value, (float(fnumber), float(shutterSpeed), float(iso))))
        inputs.sort()

        exposureGroups = []
        exposures = []
        prevFnumber = 0.0
        prevShutterSpeed = 0.0
        prevIso = 0.0
        prevPath = None  # Stores the dirname of the previous parsed image
        prevExposure = None
        newGroup = False  # True if a new exposure group needs to be created (useful when there are several datasets)
        for path, exp in inputs:
            # If the dirname of the previous image and the dirname of the current image do not match, this means that the
            # dataset that is being parsed has changed. A new group needs to be created but will fail to be detected in the
            # next "if" statement if the new dataset's exposure levels are different. Setting "newGroup" to True prevents this
            # from happening.
            if prevPath is not None and prevPath != os.path.dirname(path):
                newGroup = True

            currentExposure = LdrToHdrSampling.getExposure(exp)

            # Create a new group if the current image's exposure level is smaller than the previous image's, or
            # if a new dataset has been detected (with a change in the path of the images).
            if prevExposure and currentExposure < prevExposure or newGroup:
                exposureGroups.append(exposures)
                exposures = [exp]
            else:
                exposures.append(exp)

            prevPath = os.path.dirname(path)
            prevExposure = currentExposure
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
                bestCount = bestTuple[1]
                node.outliersNb = len(inputs) - (bestBracketSize * bestCount)  # Compute number of outliers
                node.nbBrackets.value = bestBracketSize

    @staticmethod
    def getExposure(exp, refIso = 100.0, refFnumber = 1.0):
        fnumber, shutterSpeed, iso = exp

        validShutterSpeed = shutterSpeed > 0.0 and math.isfinite(shutterSpeed)
        validFnumber = fnumber > 0.0 and math.isfinite(fnumber)

        if not validShutterSpeed and not validFnumber:
            return -1.0

        validRefFnumber = refFnumber > 0.0 and math.isfinite(refFnumber)

        if not validShutterSpeed:
            shutterSpeed = 1.0 / 200.0

        if not validFnumber:
            if validRefFnumber:
                fnumber = refFnumber
            else:
                fnumber = 2.0

        lRefFnumber = refFnumber
        if not validRefFnumber:
            lRefFnumber = fnumber

        isoToAperture = 1.0
        if iso > 1e-6 and refIso > 1e-6:
            isoToAperture = math.sqrt(iso / refIso)

        newFnumber = fnumber * isoToAperture
        expIncrease = (lRefFnumber / newFnumber) * (lRefFnumber / newFnumber)

        return shutterSpeed * expIncrease
