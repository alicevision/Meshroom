from meshroom.core import desc

class CamPairs(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'CMPMVS {mvsConfigValue} --computeCamPairs'

    mvsConfig = desc.FileAttribute(
            label='MVS Configuration file',
            description='',
            value=None,
            shortName='',
            arg='',
            uid=[0],
            isOutput=False,
            )
