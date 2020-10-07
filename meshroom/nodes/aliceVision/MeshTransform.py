__version__ = "3.0"

from meshroom.core import desc

import os.path


class MeshTransform(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_meshTransform {allParams}'
    size = desc.DynamicNodeSize('input')

    documentation = '''
This node allows to change the coordinate system of a Mesh.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''Mesh file .''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='method',
            label='Transformation Method',
            description="Transformation method:\n"
                        " * manual: Apply the gizmo transformation (show the transformed input)\n",
            value='manual',
            values=['manual'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.GroupAttribute(
            name="manualTransform",
            label="Manual Transform (Gizmo)",
            description="Translation, rotation (Euler ZXY) and uniform scale.",
            groupDesc=[
                desc.GroupAttribute(
                    name="manualTranslation",
                    label="Translation",
                    description="Translation in space.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        )
                    ],
                    joinChar=","
                ),
                desc.GroupAttribute(
                    name="manualRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler degrees.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="Euler X Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-90.0, 90.0, 1)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Euler Y Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Euler Z Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        )
                    ],
                    joinChar=","
                ),
                desc.FloatParam(
                    name="manualScale", 
                    label="Scale", 
                    description="Uniform Scale.",
                    value=1.0,
                    uid=[0],
                    range=(0.0, 20.0, 0.01)
                )
            ],
            joinChar=",",
            enabled=lambda node: node.method.value == "manual",
        ),
        desc.FloatParam(
            name='scale',
            label='Additional Scale',
            description='Additional scale to apply.',
            value=1.0,
            range=(0.0, 100.0, 0.1),
            uid=[0],
        ),
        desc.BoolParam(
            name='applyScale',
            label='Scale',
            description='Apply scale transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name='applyRotation',
            label='Rotation',
            description='Apply rotation transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name='applyTranslation',
            label='Translation',
            description='Apply translation transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
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
            label='Output SfMData File',
            description='''Aligned SfMData file .''',
            value=lambda attr: desc.Node.internalFolder + os.path.basename(attr.node.input.value),
            uid=[],
        ),
    ]
