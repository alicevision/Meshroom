__version__ = "1.0"

from meshroom.core import desc


class SfMColorHarmonize(desc.CommandLineNode):
	commandLine = 'aliceVision_utils_sfmColorHarmonize {allParams}'
	size = desc.DynamicNodeSize('input')

	category = 'Utils'
	documentation = '''Color Harmonization Node'''

	inputs = [
		desc.File(
            name='input',
            label='SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='featuresFolder',
                label='Features Folder',
                description='',
                value='',
                uid=[0],
            ),
            name='featuresFolders',
            label='Features Folders',
            description='Folder(s) containing the extracted features and descriptors.'
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='matchesFolder',
                label='Matches Folder',
                description='',
                value='',
                uid=[0],
            ),
            name='matchesFolders',
            label='Matches Folders',
            description='Folder(s) in which computed matches are stored.'
        ), 
        desc.IntParam(
        	name='referenceImage', 
        	label='Reference Image ID', 
        	description='Reference Image ID', 
        	value=0,
            range=(0, 50000, 1),
        	uid=[0], 
        	advanced=True
        ),
        desc.ChoiceParam(
            name='selectionMethod',
            label='Selection Method',
            description='Histogram selection Method',
            value='full_frame',
            values=['full_frame', 'matched_points', 'VLD_segments'],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[0],
        )
	]

	outputs = [
		desc.File(
            name='output',
            label='Folder',
            description='Output Folder.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
	]
