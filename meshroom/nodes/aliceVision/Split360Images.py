__version__ = "2.0"

from meshroom.core import desc


class Split360Images(desc.CommandLineNode):
	commandLine = 'aliceVision_utils_split360Images {allParams}'

	inputs = [
		desc.File(
			name='input',
			label='Images Folder',
			description='Images Folder',
			value='',
			uid=[0],
        ),
		desc.ChoiceParam(
			name='splitMode',
			label='Split Mode',
			description='''Split mode (equirectangular, dualfisheye)''',
			value='equirectangular',
			values=['equirectangular', 'dualfisheye'],
			exclusive=True,
			uid=[0],
		),
		desc.ChoiceParam(
			name='dualFisheyeSplitPreset',
			label='Dual Fisheye Split Preset',
			description='''Dual-Fisheye split type preset (center, top, bottom)''',
			value='center',
			values=['center', 'top', 'bottom'],
			exclusive=True,
			uid=[0],
		),
		desc.IntParam(
			name='equirectangularNbSplits',
			label='Equirectangular Nb Splits',
			description='''Equirectangular number of splits''',
			value=2,
			range=(1, 100, 1),
			uid=[0],
		),
		desc.IntParam(
			name='equirectangularSplitResolution',
			label='Equirectangular Split Resolution',
			description='''Equirectangular split resolution''',
			value=1200,
			range=(100, 10000, 1),
			uid=[0],
		),
		desc.ChoiceParam(
			name='equirectangularDemoMode',
			label='Equirectangular Demo Mode',
			description='''Export a SVG file that simulate the split''',
			value='0',
			values=['0', '1'],
			exclusive=True,
			uid=[0],
		),
	]

	outputs = [
		desc.File(
			name='output',
			label='Output Folder',
			description='''Output folder for extracted frames.''',
			value=desc.Node.internalFolder,
			uid=[],
		),
	]
