__version__ = "2.0"

from meshroom.core import desc


class MeshFiltering(desc.CommandLineNode):
    commandLine = 'aliceVision_meshFiltering {allParams}'

    documentation = '''
This node applies a Laplacian filtering to remove local defects from the raw Meshing cut.

'''

    inputs = [
        desc.File(
            name='inputMesh',
            label='Mesh',
            description='''Input Mesh (OBJ file format).''',
            value='',
            uid=[0],
            ),
        desc.FloatParam(
            name='removeLargeTrianglesFactor',
            label='Filter Large Triangles Factor',
            description='Remove all large triangles. We consider a triangle as large if one edge is bigger than N times the average edge length. Put zero to disable it.',
            value=60.0,
            range=(1.0, 100.0, 0.1),
            uid=[0],
            ),
        desc.BoolParam(
            name='keepLargestMeshOnly',
            label='Keep Only the Largest Mesh',
            description='Keep only the largest connected triangles group.',
            value=False,
            uid=[0],
            ),
        desc.IntParam(
            name='iterations',
            label='Smoothing Iterations',
            description='Number of smoothing iterations',
            value=5,
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
            advanced=True,
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
            name='outputMesh',
            label='Mesh',
            description='''Output mesh (OBJ file format).''',
            value=desc.Node.internalFolder + 'mesh.obj',
            uid=[],
            ),
    ]
