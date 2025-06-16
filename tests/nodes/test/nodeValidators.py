from meshroom.core import desc
from meshroom.core.desc.validators import NotEmptyValidator, RangeValidator


class NodeWithValidators(desc.CommandLineNode):

    inputs = [
        desc.StringParam(
            name='mandatory',
            label='Mandatory input',
            description='''''',
            value='',
            validators= [
                NotEmptyValidator()
            ]
        ),
        desc.FloatParam(
            name='floatRange',
            label='range input',
            description='''''',
            value=0.0,
            validators=[
                RangeValidator(min=0.0, max=1.0)
            ]
        ),
        desc.IntParam(
            name='intRange',
            label='range input',
            description='''''',
            value=0.0,
        ),

    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''''',
            value='{nodeCacheFolder}/appendText.txt',
        )
    ]

