import sys
from collections import OrderedDict
import os

from meshroom.core import desc


Viewpoint = OrderedDict([
            ("image", desc.File(label="Image", description="Image filepath", value="", uid=[0], isOutput=False)),
            ("focal", desc.FloatParam(label="Focal Length", description="Focal Length", value=0.0, uid=[0], range=(5, 200, 1))),
])


class CameraInit(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_cameraInit {allParams}'

    viewpoints = desc.ListAttribute(
            elementDesc=desc.GroupAttribute(label="Viewpoint", description="", groupDesc=Viewpoint, group='allParams'),
            label="Viewpoints",
            description="Input viewpoints",
            group=""
            )
    imageDirectory = desc.File(
            label='Image Directory',
            description='''Input images folder.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    jsonFile = desc.File(
            label='Json File',
            description='''Input file with all the user options. '''
            '''It can be used to provide a list of images instead of a directory.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    sensorDatabase = desc.File(
            label='Sensor Database',
            description='''Camera sensor width database path.''',
            value=os.environ.get('ALICEVISION_SENSOR_DB', ''),
            uid=[0],
            isOutput=False,
            )
    output = desc.File(
            label='Output',
            description='''Output directory for the new SfMData file Optional parameters:''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
            isOutput=True,
            )
    outputSfm = desc.File(
            label='Output SfM',
            description='''''',
            value='{cache}/{nodeType}/{uid0}/sfm_data.json',
            uid=[],
            isOutput=True,
            group='',  # not a command line argument
            )
    defaultFocalLengthPix = desc.IntParam(
            label='Default Focal Length Pix',
            description='''Focal length in pixels.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    defaultSensorWidth = desc.IntParam(
            label='Default Sensor Width',
            description='''Sensor width in mm.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    defaultIntrinsics = desc.StringParam(
            label='Default Intrinsics',
            description='''Intrinsics Kmatrix "f;0;ppx;0;f;ppy;0;0;1".''',
            value='',
            uid=[0],
            )
    defaultCameraModel = desc.ChoiceParam(
            label='Default Camera Model',
            description='''Camera model type (pinhole, radial1, radial3, brown, fisheye4).''',
            value='',
            values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4'],
            exclusive=True,
            uid=[0],
            )
    groupCameraModel = desc.ChoiceParam(
            label='Group Camera Model',
            description='''* 0: each view have its own camera intrinsic parameters '''
                        '''* 1: view share camera intrinsic parameters based on metadata, '''
                        '''if no metadata each view has its own camera intrinsic parameters '''
                        '''* 2: view share camera intrinsic parameters based on metadata, '''
                        '''if no metadata they are grouped by folder''',
            value=1,
            values=[0, 1, 2],
            exclusive=True,
            uid=[0],
            )
    verboseLevel = desc.ChoiceParam(
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
            )
