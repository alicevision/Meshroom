__version__ = "1.0"

from meshroom.core import desc


class LDRToHDR(desc.CommandLineNode):
    commandLine = 'aliceVision_convertLDRToHDR {allParams}'

    category = 'Utils'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="List of LDR images or a folder containing them ",
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='calibrationMethod',
            label='Calibration Method',
            description="Method used for camera calibration \n"
                        " * linear \n"
                        " * robertson \n"
                        " * debevec \n"
                        " * beta: grossberg",
            values=['linear', 'robertson', 'debevec', 'grossberg'],
            value='linear',
            exclusive=True,
            uid=[0],
            ),
        desc.File(
            name='inputResponse',
            label='Input Response',
            description="external camera response file path to fuse all LDR images together.",
            value='',
            uid=[0],
            ),
        desc.StringParam(
            name='targetExposureImage',
            label='Target Exposure Image',
            description="LDR image at the target exposure for the output HDR image to be centered.",
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='calibrationWeight',
            label='Calibration Weight',
            description="Weight function type (default, gaussian, triangle, plateau).",
            value='default',
            values=['default', 'gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
            ),
        desc.ChoiceParam(
            name='fusionWeight',
            label='Fusion Weight',
            description="Weight function used to fuse all LDR images together (gaussian, triangle, plateau).",
            value='gaussian',
            values=['gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
            ),
        desc.FloatParam(
            name='oversaturatedCorrection',
            label='Oversaturated Correction',
            description="Oversaturated correction for pixels oversaturated in all images: \n"
                        " - use 0 for no correction \n"
                        " - use 0.5 for interior lighting \n" 
                        " - use 1 for outdoor lighting",
            value=1,
            range=(0, 1, 0.1),
            uid=[0],
            ),
        desc.File(
            name='recoverPath',
            label='Recover Path',
            description="Path to write recovered LDR image at the target exposure by applying inverse response on HDR image.",
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
            ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description="Output HDR image path.",
            value=desc.Node.internalFolder + 'hdr.exr',
            uid=[],
            ),
        desc.File(
            name='outputResponse',
            label='Output Response',
            description="Output response function path.",
            value=desc.Node.internalFolder + 'response.ods',
            uid=[],
            ),
    ]
