from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class FloatToIntRound(AttributeConverter):
    description = (
        "Convert a FloatParam to an IntParam by rounding the value."
    )

    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(round(value))


class FloatToIntTruncate(AttributeConverter):
    description = (
        "Convert a FloatParam to an IntParam by truncating the value."
    )

    priority = 20
    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(value)
