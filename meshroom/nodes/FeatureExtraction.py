
from meshroom.processGraph import desc

class FeatureExtraction(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'openMVG_main_ComputeFeatures {allParams}'

    input_file = desc.FileAttribute(
            label='Input File',
            description='''a SfM_Data file''',
            value='',
            shortName='i',
            arg='',
            uid=[0],
            isOutput=False,
            )
    outdir = desc.FileAttribute(
            label='Outdir',
            description='''output path for the features and descriptors files (*.feat, *.desc) [Optional]''',
            value='{cache}/{nodeType}/{uid0}/',
            shortName='o',
            arg='path',
            uid=[0],
            isOutput=True,
            )
    force = desc.ParamAttribute(
            label='Force',
            description='''Force to recompute data''',
            value='',
            shortName='f',
            arg='',
            uid=[0],
            isOutput=False,
            )
    describerMethods = desc.ParamAttribute(
            label='Describer Methods',
            description='''(methods to use to describe an image): SIFT (default), SIFT_FLOAT to use SIFT stored as float, AKAZE: AKAZE with floating point descriptors, AKAZE_MLDB: AKAZE with binary descriptors''',
            value='',
            shortName='m',
            arg='',
            uid=[0],
            isOutput=False,
            )
    upright = desc.ParamAttribute(
            label='Upright',
            description='''Use Upright feature 0 or 1''',
            value='',
            shortName='u',
            arg='',
            uid=[0],
            isOutput=False,
            )
    describerPreset = desc.ParamAttribute(
            label='Describer Preset',
            description='''(used to control the Image_describer configuration): LOW, MEDIUM, NORMAL (default), HIGH, ULTRA: !!Can take long time!!''',
            value='',
            shortName='p',
            arg='',
            uid=[0],
            isOutput=False,
            )
    jobs = desc.ParamAttribute(
            label='Jobs',
            description='''Specifies the number of jobs to run simultaneously. Use -j 0 for automatic mode. Unrecognized option --help''',
            value='',
            shortName='j',
            arg='',
            uid=[0],
            isOutput=False,
            )