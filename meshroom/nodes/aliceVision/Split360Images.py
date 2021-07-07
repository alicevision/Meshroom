__version__ = "1.0"

from meshroom.core import desc

class Split360Images(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_split360Images {allParams}'
    
    category = 'Utils'
    documentation = '''This node is used to extract multiple images from equirectangular or dualfisheye images or image folder'''

    inputs = [
        desc.File(
            name='input',
            label='Images Folder',
            description="Images Folder",
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
                    name='dualFisheyeSplitPreset',
                    label='Split Preset',
                    description="Dual-Fisheye split type preset (center, top, bottom)",
                    value='center',
                    values=['center', 'top', 'bottom'],
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
                    name='equirectangularDemoMode',
                    label='Demo Mode',
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
            label='Output Folder',
            description="Output folder for extracted frames.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
