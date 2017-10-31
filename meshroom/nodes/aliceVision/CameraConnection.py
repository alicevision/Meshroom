from meshroom.core import desc

class CameraConnection(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_cameraConnection --ini {mvsConfigValue}'

    mvsConfig = desc.File(
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            isOutput=False,
            )
