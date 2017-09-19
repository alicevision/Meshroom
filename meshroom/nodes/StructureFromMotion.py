
from meshroom.processGraph import desc

class StructureFromMotion(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'openMVG_main_IncrementalSfM {allParams}'

    input_file = desc.FileAttribute(
            label='Input File',
            description='''path to a SfM_Data scene''',
            value='',
            shortName='i',
            arg='',
            uid=[0],
            isOutput=False,
            )
    describerMethods = desc.ParamAttribute(
            label='Describer Methods',
            description='''(methods to use to describe an image): SIFT (default), SIFT_FLOAT to use SIFT stored as float, AKAZE: AKAZE with floating point descriptors, AKAZE_MLDB: AKAZE with binary descriptors''',
            value='SIFT',
            shortName='d',
            arg='',
            uid=[0],
            isOutput=False,
            )
    matchdir = desc.FileAttribute(
            label='Matchdir',
            description='''path to the matches that corresponds to the provided SfM_Data scene''',
            value='',
            shortName='m',
            arg='',
            uid=[0],
            isOutput=False,
            )
    featuresDir = desc.FileAttribute(
            label='Features Dir',
            description='''path to directory containing the extracted features (default: $matchdir)''',
            value='',
            shortName='F',
            arg='',
            uid=[0],
            isOutput=False,
            )
    outdir = desc.FileAttribute(
            label='Outdir',
            description='''path where the output data will be stored''',
            value='{cache}/{nodeType}/{uid0}/',
            shortName='o',
            arg='',
            uid=[0],
            isOutput=True,
            )
    out_sfmdata_file = desc.FileAttribute(
            label='Out Sfmdata File',
            description='''path of the output sfmdata file (default: $outdir/sfm_data.json)''',
            value='{cache}/{nodeType}/{uid0}/sfm.json',
            shortName='s',
            arg='',
            uid=[0],
            isOutput=True,
            )
    inter_file_extension = desc.FileAttribute(
            label='Inter File Extension',
            description='''extension of the intermediate file export (default: .ply)''',
            value='.ply',
            shortName='e',
            arg='',
            uid=[0],
            isOutput=False,
            )
    # initialPairA = desc.FileAttribute(
    #         label='Initial Pair A',
    #         description='''filename of the first image (without path)''',
    #         value='',
    #         shortName='a',
    #         arg='',
    #         uid=[0],
    #         isOutput=False,
    #         )
    # initialPairB = desc.FileAttribute(
    #         label='Initial Pair B',
    #         description='''filename of the second image (without path)''',
    #         value='',
    #         shortName='b',
    #         arg='',
    #         uid=[0],
    #         isOutput=False,
    #         )
    camera_model = desc.ParamAttribute(
            label='Camera Model',
            description='''Camera model type for view with unknown intrinsic: 1: Pinhole 2: Pinhole radial 1 3: Pinhole radial 3 (default)''',
            value=3,
            shortName='c',
            arg='',
            uid=[0],
            isOutput=False,
            )
    refineIntrinsics = desc.ParamAttribute(
            label='Refine Intrinsics',
            description='''0-> intrinsic parameters are kept as constant 1-> refine intrinsic parameters (default).''',
            value=1,
            shortName='f',
            arg='',
            uid=[0],
            isOutput=False,
            )
    minInputTrackLength = desc.ParamAttribute(
            label='Min Input Track Length',
            description='''minimum track length in input of SfM (default: 2)''',
            value=2,
            shortName='t',
            arg='N',
            uid=[0],
            isOutput=False,
            )
    # matchFilePerImage = desc.FileAttribute(
    #         label='Match File Per Image',
    #         description='''To use one match file per image instead of a global file.''',
    #         value=1,
    #         shortName='p',
    #         arg='',
    #         uid=[0],
    #         isOutput=False,
    #         )
    allowUserInteraction = desc.ParamAttribute(
            label='Allow User Interaction',
            description='''Enable/Disable user interactions. (default: true) If the process is done on renderfarm, it doesn't make sense to wait for user inputs. Unrecognized option --help''',
            value=0,
            shortName='u',
            arg='',
            uid=[0],
            isOutput=False,
            )