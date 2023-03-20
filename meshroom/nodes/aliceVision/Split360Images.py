__version__ = "2.0"

from meshroom.core import desc

class Split360Images(desc.AVCommandLineNode):
    commandLine = 'aliceVision_split360Images {allParams}'
    
    category = 'Utils'
    documentation = "This node is used to extract multiple images from equirectangular or dualfisheye images."

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="Single image, image folder or SfMData file.",
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='splitMode',
            label='Split Mode',
            description="Split mode (equirectangular, dualfisheye)",
            value='equirectangular',
            values=['equirectangular', 'dualfisheye'],
            exclusive=True,
            uid=[0],
        ),
        desc.GroupAttribute(name="dualFisheyeGroup", label="Dual Fisheye", description="Dual Fisheye", group=None,
            enabled=lambda node: node.splitMode.value == 'dualfisheye',
            groupDesc=[
                desc.ChoiceParam(
                    name='dualFisheyeOffsetPresetX',
                    label='X Offset Preset',
                    description="Dual-Fisheye X offset preset",
                    value='center',
                    values=['center', 'left', 'right'],
                    exclusive=True,
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name='dualFisheyeOffsetPresetY',
                    label='Y Offset Preset',
                    description="Dual-Fisheye Y offset preset",
                    value='center',
                    values=['center', 'top', 'bottom'],
                    exclusive=True,
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name='dualFisheyeCameraModel',
                    label='Camera Model',
                    description="Dual-Fisheye camera model",
                    value='fisheye4',
                    values=['fisheye4', 'equidistant_r3'],
                    exclusive=True,
                    uid=[0],
                ),
            ]
        ),
        desc.GroupAttribute(name="equirectangularGroup", label="Equirectangular", description="Equirectangular", group=None,
            enabled=lambda node: node.splitMode.value == 'equirectangular',
            groupDesc=[
                desc.IntParam(
                    name='equirectangularNbSplits',
                    label='Nb Splits',
                    description="Equirectangular number of splits",
                    value=2,
                    range=(1, 100, 1),
                    uid=[0],
                ),
                desc.IntParam(
                    name='equirectangularSplitResolution',
                    label='Split Resolution',
                    description="Equirectangular split resolution",
                    value=1200,
                    range=(100, 10000, 1),
                    uid=[0],
                ),
                desc.BoolParam(
                    name='equirectangularPreviewMode',
                    label='Preview Mode',
                    description="Export a SVG file that simulates the split",
                    value=False,
                    uid=[0],
                ),
                desc.FloatParam(
                    name='fov',
                    label='Field of View',
                    description="Field of View to extract (in degree)",
                    value=110.0,
                    range=(0.0, 180.0, 1.0),
                    uid=[0],
                ),
            ]
        ),
        desc.ChoiceParam(
            name='extension',
            label='Output File Extension',
            description='Output Image File Extension.',
            value='',
            values=['', 'exr', 'jpg', 'tiff', 'png'],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Folder',
            description="Output folder for extracted frames.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='outSfMData',
            label='SfMData file',
            description="Output SfMData file.",
            value=desc.Node.internalFolder + 'rig.sfm',
            uid=[],
        ),
    ]
