__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class LightingEstimation(desc.AVCommandLineNode):
    commandLine = 'aliceVision_lightingEstimation {allParams}'

    category = 'Utils'
    documentation = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ), 
        desc.File(
            name="depthMapsFilterFolder",
            label="Filtered Depth Maps Folder",
            description="Input filtered depth maps folder.",
            value="",
        ),
        desc.File(
            name="imagesFolder",
            label="Images Folder",
            description="Use images from a specific folder instead of those specify in the SfMData file.\n"
                        "Filename should be the image UID.",
            value="",
        ),
        desc.ChoiceParam(
            name="lightingEstimationMode",
            label="Lighting Estimation Mode",
            description="Lighting estimation mode.",
            value="global",
            values=["global", "per_image"],
            advanced=True,
        ),
        desc.ChoiceParam(
            name="lightingColor",
            label="Lighting Color Mode",
            description="Lighting color mode.",
            value="RGB",
            values=["RGB", "Luminance"],
            advanced=True,
        ),
        desc.ChoiceParam(
            name="albedoEstimationName",
            label="Albedo Estimation Name",
            description="Albedo estimation method used for light estimation.",
            value="constant",
            values=["constant", "picture", "median_filter", "blur_filter"],
            advanced=True,
        ),
        desc.IntParam(
            name="albedoEstimationFilterSize",
            label="Albedo Estimation Filter Size",
            description="Albedo filter size for estimation method using filter.",
            value=3,
            range=(0, 100, 1),
            advanced=True,
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
            description="Folder for output lighting vector files.",
            value=desc.Node.internalFolder,
        ),
    ]
