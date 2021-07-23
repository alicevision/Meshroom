__version__ = "1.0"

from meshroom.core import desc
import os.path

currentDir = os.path.dirname(os.path.abspath(__file__))

class RenderAnimatedCamera(desc.CommandLineNode):
    commandLine = '{blenderPathValue} -b --python {scriptPathValue} -- {allParams}'

    category = 'Export'
    documentation = '''
        This node makes a rendering of the sfmData scene through an animated camera using the Blender rendering engine.
        It supports both Point Clouds (.abc) and Meshes (.obj).
    '''

    inputs = [
        desc.File(
            name='blenderPath',
            label='Blender Path',
            description='''Path to blender executable''',
            value=os.environ.get('BLENDER',"C:/Program Files/Blender Foundation/Blender 2.91/blender.exe"),
            uid=[],
            group='',
        ),
        desc.File(
            name='scriptPath',
            label='Script Path',
            description='''Path to the internal script for rendering in Blender''',
            value=os.path.join(currentDir, 'scripts' ,'renderAnimatedCameraInBlender.py'),
            uid=[],
            group='',
        ),
        desc.File(
            name='sfmCameraPath',
            label='SfmData with Animated Camera',
            description='''SfmData with the animated camera to render''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='model',
            label='Model',
            description='Point Cloud or Mesh used in the rendering',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='useBackground',
            label='Display Background',
            description='Use the undistorted images as background',
            value=True,
            uid=[0],
        ),
        desc.File(
            name='undistortedImages',
            label='Undistorted Images Folder',
            description='''Input folder with the undistorted images''',
            value='',
            uid=[0],
            enabled=lambda node: node.useBackground.value,
        ),
        desc.GroupAttribute(
            name="pointCloudParams",
            label="Point Cloud Settings",
            group=None,
            enabled=lambda node: node.model.value.lower().endswith('.abc'),
            description="Setting of the render if we use a Point Cloud",
            groupDesc=[
                desc.FloatParam(
                    name='pointCloudDensity',
                    label='Density',
                    description='''Reduce the points density for the point cloud rendering''',
                    value=0.25,
                    range=(0.01, 0.5, 0.01),
                    uid=[0],
                ),
                desc.FloatParam(
                    name='particleSize',
                    label='Particle Size',
                    description='''Scale of particles used to show the point cloud''',
                    value=0.1,
                    range=(0.01, 1, 0.01),
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name='particleColor',
                    label='Particle Color',
                    description='''Color of particles used to show the point cloud''',
                    value='Red',
                    values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
                    exclusive=True,
                    uid=[0],
                    joinChar=',',
                ),
            ]
        ),
        desc.GroupAttribute(
            name="meshParams",
            label="Mesh Settings",
            group=None,
            enabled=lambda node: node.model.value.lower().endswith('.obj'),
            description="Setting of the render if we use a Mesh",
            groupDesc=[
                desc.ChoiceParam(
                    name='edgeColor',
                    label='Edge Color',
                    description='''Color of the edges of the rendered object''',
                    value='Red',
                    values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
                    exclusive=True,
                    uid=[0],
                    joinChar=',',
                ),
            ]
        ),
        desc.ChoiceParam(
            name='videoFormat',
            label='Video Format',
            description='''Choose the format of the output among this list of supported format''',
            value='mkv',
            values=['mkv', 'mp4', 'mov', 'avi'],
            exclusive=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='outputPath',
            label='Output Path',
            description='''Output Folder''',
            value=desc.Node.internalFolder,
            uid=[],
        )
    ]