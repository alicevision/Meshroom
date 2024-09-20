__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class Split360InputNodeSize(desc.DynamicNodeSize):
    '''
    The Split360Images will increase the amount of views in the SfMData.
    This class converts the number of input views into the number of split output views.
    '''
    def computeSize(self, node):
        s = super(Split360InputNodeSize, self).computeSize(node)
        factor = 0
        mode = node.attribute('splitMode')
        if mode.value == 'equirectangular':
            factor = node.attribute('equirectangularGroup.equirectangularNbSplits').value
        elif mode.value == 'dualfisheye':
            factor = 2
        return s * factor


class Split360Images(desc.AVCommandLineNode):
    commandLine = 'aliceVision_split360Images {allParams}'
    size = Split360InputNodeSize('input')
    
    category = 'Utils'
    documentation = "This node is used to extract multiple images from equirectangular or dualfisheye images."

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Single image, image folder or SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="splitMode",
            label="Split Mode",
            description="Split mode (equirectangular, dualfisheye).",
            value="equirectangular",
            values=["equirectangular", "dualfisheye"],
        ),
        desc.GroupAttribute(
            name="dualFisheyeGroup",
            label="Dual Fisheye",
            description="Dual Fisheye.",
            group=None,
            enabled=lambda node: node.splitMode.value == "dualfisheye",
            groupDesc=[
                desc.ChoiceParam(
                    name="dualFisheyeOffsetPresetX",
                    label="X Offset Preset",
                    description="Dual-Fisheye X offset preset.",
                    value="center",
                    values=["center", "left", "right"],
                ),
                desc.ChoiceParam(
                    name="dualFisheyeOffsetPresetY",
                    label="Y Offset Preset",
                    description="Dual-Fisheye Y offset preset.",
                    value="center",
                    values=["center", "top", "bottom"],
                ),
                desc.ChoiceParam(
                    name="dualFisheyeCameraModel",
                    label="Camera Model",
                    description="Dual-Fisheye camera model.",
                    value="fisheye4",
                    values=["fisheye4", "equidistant_r3"],
                ),
            ],
        ),
        desc.GroupAttribute(
            name="equirectangularGroup",
            label="Equirectangular",
            description="Equirectangular",
            group=None,
            enabled=lambda node: node.splitMode.value == "equirectangular",
            groupDesc=[
                desc.IntParam(
                    name="equirectangularNbSplits",
                    label="Nb Splits",
                    description="Equirectangular number of splits.",
                    value=2,
                    range=(1, 100, 1),
                ),
                desc.IntParam(
                    name="equirectangularSplitResolution",
                    label="Split Resolution",
                    description="Equirectangular split resolution.",
                    value=1200,
                    range=(100, 10000, 1),
                ),
                desc.BoolParam(
                    name="equirectangularPreviewMode",
                    label="Preview Mode",
                    description="Export a SVG file that simulates the split.",
                    value=False,
                ),
                desc.FloatParam(
                    name="fov",
                    label="Field Of View",
                    description="Field of View to extract (in degrees).",
                    value=110.0,
                    range=(0.0, 180.0, 1.0),
                ),
            ],
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Output image file extension.",
            value="",
            values=["", "exr", "jpg", "tiff", "png"],
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
            label="Folder",
            description="Output folder for extracted frames.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outSfMData",
            label="SfMData File",
            description="Output SfMData file.",
            value=desc.Node.internalFolder + "rig.sfm",
        ),
    ]
