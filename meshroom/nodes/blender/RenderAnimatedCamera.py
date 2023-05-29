__version__ = "2.0"

from meshroom.core import desc
import os.path

currentDir = os.path.dirname(os.path.abspath(__file__))

class RenderAnimatedCamera(desc.CommandLineNode):
    commandLine = '{blenderCmdValue} -b --python {scriptValue} -- {allParams}'

    category = 'Visualization'
    documentation = '''
        This node makes a rendering of the sfmData scene through an animated camera using the Blender rendering engine.
        It supports both Point Clouds (.abc) and Meshes (.obj).
    '''

    inputs = [
        desc.File(
            name='blenderCmd',
            label='Blender Command',
            description='Command to launch Blender',
            value='blender',
            uid=[],
            group='',
        ),
        desc.File(
            name='script',
            label='Script Path',
            description='Path to the internal script for rendering in Blender',
            value=os.path.join(currentDir, 'scripts' ,'renderAnimatedCameraInBlender.py'),
            uid=[],
            group='',
            advanced=True,
        ),
        desc.File(
            name='cameras',
            label='SfmData with Animated Camera',
            description='SfmData with the animated camera to render (in json format)',
            value='',
            uid=[0],
        ),
        desc.File(
            name='model',
            label='Model',
            description='Point Cloud or Mesh to render',
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
            description='Input folder with the undistorted images',
            value='',
            uid=[0],
            enabled=lambda node: node.useBackground.value,
        ),
        desc.GroupAttribute(
            name="pointCloudParams",
            label="Point Cloud Settings",
            group=None,
            enabled=lambda node: node.model.value.lower().endswith('.abc'),
            description="Settings of the render if we use a Point Cloud",
            groupDesc=[
                desc.FloatParam(
                    name='particleSize',
                    label='Particle Size',
                    description='Scale of particles used to show the point cloud',
                    value=0.01,
                    range=(0.01, 1.0, 0.01),
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name='particleColor',
                    label='Particle Color',
                    description='Color of particles used to show the point cloud',
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
                    name='shading',
                    label='Shading',
                    description='Shading method for visualizing the mesh',
                    value='wireframe',
                    values=['wireframe', 'line_art'],
                    exclusive=True,
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name='edgeColor',
                    label='Edge Color',
                    description='Color of the edges of the rendered object',
                    value='Red',
                    values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
                    exclusive=True,
                    uid=[0],
                ),
            ]
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description='Output Folder',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='render',
            label='Render',
            description='Frames rendered in Blender',
            semantic='image',
            value=desc.Node.internalFolder + '<VIEW_ID>.png',
            uid=[],
            group='',
        ),
    ]