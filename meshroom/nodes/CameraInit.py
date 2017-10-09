
from meshroom.core import desc

class CameraInit(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'openMVG_main_SfMInit_ImageListing {allParams}'

    imageDirectory = desc.FileAttribute(
            label='Image Directory',
            description='''''',
            value='',
            shortName='i',
            arg='',
            uid=[0],
            isOutput=False,
            )
    jsonFile = desc.FileAttribute(
            label='Json File',
            description='''Input file with all the user options. It can be used to provide a list of images instead of a directory.''',
            value='',
            shortName='j',
            arg='',
            uid=[0],
            isOutput=False,
            )
    sensorWidthDatabase = desc.FileAttribute(
            label='Sensor Width Database',
            description='''''',
            value='',
            shortName='d',
            arg='',
            uid=[0],
            isOutput=False,
            )
    outputDirectory = desc.FileAttribute(
            label='Output Directory',
            description='''''',
            value='{cache}/{nodeType}/{uid0}/',
            shortName='o',
            arg='',
            isOutput=True,
            )
    outputSfm = desc.FileAttribute( # not command line
            label='Output SfM',
            description='''''',
            value='{cache}/{nodeType}/{uid0}/sfm_data.json',
            shortName='o',
            arg='',
            isOutput=True,
            group='',
            )
    focal = desc.ParamAttribute(
            label='Focal',
            description='''(pixels)''',
            value='',
            shortName='f',
            arg='',
            uid=[0],
            isOutput=False,
            )
    sensorWidth = desc.ParamAttribute(
            label='Sensor Width',
            description='''(mm)''',
            value='',
            shortName='s',
            arg='',
            uid=[0],
            isOutput=False,
            )
    intrinsics = desc.ParamAttribute(
            label='Intrinsics',
            description='''Kmatrix: "f;0;ppx;0;f;ppy;0;0;1"''',
            value='',
            shortName='k',
            arg='',
            uid=[0],
            isOutput=False,
            )
    camera_model = desc.ParamAttribute(
            label='Camera Model',
            description='''Camera model type (pinhole, radial1, radial3, brown or fisheye4)''',
            value='',
            shortName='c',
            arg='',
            uid=[0],
            isOutput=False,
            )
    group_camera_model = desc.FileAttribute(
            label='Group Camera Model',
            description='''0-> each view have its own camera intrinsic parameters, 1-> (default) view share camera intrinsic parameters based on metadata, if no metadata each view has its own camera intrinsic parameters 2-> view share camera intrinsic parameters based on metadata, if no metadata they are grouped by folder''',
            value='',
            shortName='g',
            arg='',
            uid=[0],
            isOutput=False,
            )
    use_UID = desc.ParamAttribute(
            label='Use  U I D',
            description='''Generate a UID (unique identifier) for each view. By default, the key is the image index.''',
            value='',
            shortName='u',
            arg='',
            uid=[0],
            isOutput=False,
            )
    storeMetadata = desc.ParamAttribute(
            label='Store Metadata',
            description='''Store image metadata in the sfm data Unrecognized option --help''',
            value='',
            shortName='m',
            arg='',
            uid=[0],
            isOutput=False,
            )
