__version__ = "1.0"

from meshroom.core import desc


class LDRToHDR(desc.CommandLineNode):
    commandLine = 'aliceVision_convertLDRToHDR {allParams}'

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name='inputFolder',
                label='Input File/Folder',
                description="LDR image or folder of LDR images.",
                value='',
                uid=[0],
                ),
            name="input",
            label="Input Files or Folders",
            description='LDR images or folders of LDR images.',
        ),
        desc.BoolParam(
            name='fisheyeLens',
            label='Fisheye Lens',
            description="True if a fisheye lens has been used.\n"
                        "This will improve the estimation of the Camera's Response Function by considering only the pixels in the center of the image\n"
                        "and thus ignore undefined/noisy pixels outside the circle defined by the fisheye lens.",
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='calibrationMethod',
            label='Calibration Method',
            description="Method used for camera calibration \n"
                        " * linear \n"
                        " * robertson \n"
                        " * debevec \n"
                        " * grossberg",
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
            description="LDR image(s) name(s) specifying the target exposure to center HDR output image(s).",
            value='',
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
        desc.ChoiceParam(
            name='fusionWeight',
            label='Fusion Weight',
            description="Weight function used to fuse all LDR images together \n"
                        " * gaussian \n"
                        " * triangle \n" 
                        " * plateau",
            value='gaussian',
            values=['gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
        ),
        desc.FloatParam(
            name='expandDynamicRange',
            label='Expand Dynamic Range',
            description="Correction of clamped high values in dynamic range: \n"
                        " - use 0 for no correction \n"
                        " - use 0.5 for interior lighting \n" 
                        " - use 1 for outdoor lighting",
            value=1,
            range=(0, 1, 0.1),
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
        desc.File(
            name='recoverPath',
            label='Output Recovered Files',
            description="(debug) Folder to store recovered LDR images at target exposures, with inverted camera function.",
            advanced=True,
            value='',
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description="Output folder to store HDR images",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='outputResponse',
            label='Output Response',
            description="Path to store output response function of the camera.",
            value=desc.Node.internalFolder + 'response.csv',
            uid=[],
        ),
    ]
