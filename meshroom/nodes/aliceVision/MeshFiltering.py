import sys
from meshroom.core import desc


class MeshFiltering(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_meshFiltering {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''Input Mesh (OBJ file format).''',
            value='',
            uid=[0],
            ),
        desc.IntParam(
            name='iterations',
            label='Nb Iterations',
            description='',
            value=10,
            range=(0, 50, 1),
            uid=[0],
            ),
        desc.FloatParam(
            name='lambda',
            label='Lambda',
            description='',
            value=1.0,
            range=(0.0, 10.0, 0.1),
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
            label='Output',
            description='''Output mesh (OBJ file format).''',
            value='{cache}/{nodeType}/{uid0}/mesh.obj',
            uid=[],
            ),
    ]
