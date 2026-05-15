from meshroom.core import desc
from meshroom.core.desc.validators import NotEmptyValidator, RangeValidator, success, error


class NodeWithValidators(desc.CommandLineNode):

    inputs = [
        desc.StringParam(
            name="mandatory",
            label="Mandatory Input",
            description="",
            value="",
            validators= [
                NotEmptyValidator()
            ]
        ),
        desc.FloatParam(
            name="floatRange",
            label="Range Input",
            description="",
            value=0.0,
            validators=[
                RangeValidator(min=0.0, max=1.0)
            ]
        ),
        desc.IntParam(
            name="intRange",
            label="Range Input",
            description="",
            value=0,
            validators=[lambda node, attr: success() if 0 <= attr.value < 5 else error("Value should be in range 0-5")]
        ),

    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="{nodeCacheFolder}/appendText.txt",
        )
    ]
