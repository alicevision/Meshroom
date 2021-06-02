__version__ = "1.0"

from meshroom.core import desc
import os.path

currentDir = os.path.dirname(os.path.abspath(__file__))

class RenderAnimatedCamera(desc.CommandLineNode):
    commandLine = '{blenderPathValue} -b --python {scriptPathValue} -- {allParams}'

    category = 'Rendition'
    documentation = '''
        The goal of this node is to make a render of the sfmData a Blender scene using Blender's API.
        It supports both Point Clouds (.abc) and Meshes (.obj) and can use a background image of you use undistorted images.
        We have several inputs:
           **blenderPath points to the blender executable
           **scriptPath point to the script containing the code.
           **sfMCameraPath point to the AnimatedCamera we are going to be tracking.
           **useBackground determines if you want to use images as a background.
           **undistortedImages path toward the images you can use as background.
           **sfMData the data you want to render.
            (point cloud)
            **pointCloudDensity changes the density of the point cloud rendered.
            **particleSize changes the size of each point in the point cloud rendered.
            **particleColor changes the color of each point in the point cloud rendered. 
            (Mesh)
            **edgeColor is the color of the outline of the mesh rendered.
           **outputFormat is the video format we want to export of rendition in.
           **outputPath point to where is video is going to be saved.
    '''

    inputs = [
        desc.File(
            name='blenderPath',
            label='Blender Path',
            description='''Path to blender binary.''',
            value=os.environ.get('BLENDER',"C:/Program Files/Blender Foundation/Blender 2.91/blender.exe"),
            uid=[],
            group='',
        ),
        desc.File(
            name='scriptPath',
            label='Script Path',
            description='''Path to the script in the project.''',
            value=os.path.join(currentDir, 'scripts' ,'renderAnimatedCameraInBlender.py'),
            uid=[],
            group='',
        ),
        desc.File(
            name='sfMCameraPath',
            label='Camera Path',
            description='''Input Camera path from the sfm.''',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='useBackground',
            label='Display Background',
            description='Tick if you want to use original image dataset as background',
            value=True,
            uid=[0],
        ),
        desc.File(
            name='undistortedImages',
            label='Images Folder',
            description='''Input the processed images.''',
            value='',
            uid=[0],
            enabled=lambda node: node.displayBackground.useBackground.value,
        ),
        desc.File(
            name='sfMData',
            label='SFM Data',
            description='''Input the previously used SFM Data.''',
            value='',
            uid=[0],
        ),
        desc.GroupAttribute(name="isCloudPoint", label="Point Cloud Settings", group=None, enabled=lambda node: node.sfMData.value.endswith('.abc'), description="Setting of the render if we use a Point Cloud. (SFM Data is .abc)", groupDesc=[
            desc.FloatParam(
                name='pointCloudDensity',
                label='Point Cloud Density',
                description='''Number of point from the point cloud rendered''',
                value=0.25,
                range=(0.01, 0.5, 0.01),
                uid=[0],
                enabled=lambda node: node.sfMData.value.endswith('.abc'),
            ),
            desc.FloatParam(
                name='particleSize',
                label='Particle Size',
                description='''Scale of every particle used to show the point cloud''',
                value=0.25,
                range=(0.01, 1, 0.01),
                uid=[0],
                enabled=lambda node: node.sfMData.value.endswith('.abc'),
            ),
            desc.ChoiceParam(
                name='particleColor',
                label='Particle Color',
                description='''Color of every particle used to show the point cloud (SFM Data is .abc)''',
                value='Red',
                values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
                exclusive=True,
                uid=[0],
                joinChar=',',
                enabled=lambda node: node.sfMData.value.endswith('.abc'),
            ),
        ]),
        desc.GroupAttribute(name="isMesh", label="Mesh Settings", group=None, enabled=lambda node: node.sfMData.value.endswith('.obj'), description="Setting of the render if we use a Mesh. (SFM Data is .obj)", groupDesc=[
            desc.ChoiceParam(
                name='edgeColor',
                label='Edge Color',
                description='''Color of the edges of the rendered object (SFM Data is .obj)''',
                value='Red',
                values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
                exclusive=True,
                uid=[0],
                joinChar=',',
                enabled=lambda node: node.sfMData.value.endswith('.obj'),
            ),
        ]),
        desc.ChoiceParam(
            name='outputFormat',
            label='Output Format',
            description='''Choose the format of the output among this list of supported format''',
            value='mkv',
            values=['mkv', 'mp4', 'mov', 'avi'],
            exclusive=True,
            uid=[0],
            joinChar=',',
        ),
    ]

    outputs = [
        desc.File(
            name='outputPath',
            label='Output Path',
            description='''Output folder.''',
            value=desc.Node.internalFolder,
            uid=[],
        )
    ]