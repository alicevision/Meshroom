from meshroom.processGraph import desc

class PrepareDenseScene(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'openMVG_main_openMVG2CMPMVS2 {allParams}'

    outdir = desc.FileAttribute(
            label='Outdir',
            description='''path Invalid command line parameter.''',
            value='{cache}/{nodeType}/{uid0}/',
            shortName='o',
            arg='',
            isOutput=True,
            )
    mvsConfig = desc.FileAttribute( # not a command line arg
            label='MVS Configuration file',
            description='',
            value='{cache}/{nodeType}/{uid0}/_tmp_scale{scaleValue}/mvs.ini',
            shortName='',
            arg='',
            group='',
            isOutput=True,
            )

    sfmdata = desc.FileAttribute(
            label='Sfmdata',
            description='''filename, the SfM_Data file to convert''',
            value='',
            shortName='i',
            arg='',
            uid=[0],
            isOutput=False,
            )
    scale = desc.ParamAttribute(
            label='Scale',
            description='''downscale image factor''',
            value=2,
            shortName='s',
            arg='',
            uid=[0],
            isOutput=False,
            )
