__version__ = "1.0"

from meshroom.core import desc


class MeshDenoising(desc.CommandLineNode):
    commandLine = 'aliceVision_meshDenoising {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''Input Mesh (OBJ file format).''',
            value='',
            uid=[0],
            ),
        desc.IntParam(
            name='denoisingIterations',
            label='Denoising Iterations',
            description='''Number of denoising iterations.''',
            value=5,
            range=(0, 30, 1),
            uid=[0],
            ),
        desc.FloatParam(
            name='meshUpdateClosenessWeight',
            label='Mesh Update Closeness Weight',
            description='''Closeness weight for mesh update, must be positive.''',
            value=0.001,
            range=(0.0, 0.1, 0.001),
            uid=[0],
            ),
        desc.FloatParam(
            name='lambda',
            label='Lambda',
            description='''Regularization weight.''',
            value=2.0,
            range=(0.0, 10.0, 0.01),
            uid=[0],
            ),
        desc.FloatParam(
            name='eta',
            label='Eta',
            description='Gaussian standard deviation for spatial weight, '
                        'scaled by the average distance between adjacent face centroids.\n'
                        'Must be positive.',
            value=1.5,
            range=(0.0, 20.0, 0.01),
            uid=[0],
            ),
        desc.FloatParam(
            name='mu',
            label='Mu',
            description='''Gaussian standard deviation for guidance weight.''',
            value=1.5,
            range=(0.0, 10.0, 0.01),
            uid=[0],
            ),
        desc.FloatParam(
            name='nu',
            label='Nu',
            description='''Gaussian standard deviation for signal weight.''',
            value=0.3,
            range=(0.0, 5.0, 0.01),
            uid=[0],
            ),
        desc.ChoiceParam(
            name='meshUpdateMethod',
            label='Mesh Update Method',
            description='Mesh Update Method\n'
                        ' * ITERATIVE_UPDATE (default): ShapeUp styled iterative solver \n'
                        ' * POISSON_UPDATE: Poisson-based update from [Wang et al. 2015] "Rolling guidance normal filter for geometric processing"',
            value=0,
            values=(0, 1),
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
            label='Output',
            description='''Output mesh (OBJ file format).''',
            value=desc.Node.internalFolder + 'mesh.obj',
            uid=[],
            ),
    ]
