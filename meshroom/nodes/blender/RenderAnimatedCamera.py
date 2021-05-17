__version__ = "1.0"

from meshroom.core import desc
import os.path

currentDir = os.path.dirname(os.path.abspath(__file__))

class RenderAnimatedCamera(desc.CommandLineNode):
    commandLine = '{blenderPathValue} -b --python {scriptPathValue} -- {allParams}'

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
            description='''Path to blender binary.''',
            value=os.path.join(currentDir, 'scripts' ,'camera_support.py'),
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
        desc.File(
            name='sfMData',
            label='SFM Data',
            description='''Input the previously used SFM Data.''',
            value='',
            uid=[0],
        ),
        desc.FloatParam(
            name='cloudPointDensity',
            label='Cloud Point Density',
            description='''Number of point from the cloud rendered''',
            value=0.25,
            range=(0.01, 0.5, 0.01),
            uid=[0],
        ),
        desc.FloatParam(
            name='particleSize',
            label='Particle Size',
            description='''Scale of every particle used to show the cloud of point''',
            value=0.25,
            range=(0.01, 1, 0.01),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='particleColor',
            label='Particle Color',
            description='''Color of every particle used to show the cloud of point''',
            value=['Grey'],
            values=['Grey', 'White', 'Red', 'Green', 'Magenta'],
            exclusive=True,
            uid=[0],
            joinChar=',',
        ),
        desc.File(
            name='undistortedImages',
            label='Images Folder',
            description='''Input the processed images.''',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='outputPath',
            label='Output Video',
            description='''Output folder.''',
            value=desc.Node.internalFolder, # PLACE HOLDER TO CHANGE
            uid=[],
        )
    ]