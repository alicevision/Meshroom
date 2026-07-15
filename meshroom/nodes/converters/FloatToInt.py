from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class FloatToIntRound(AttributeConverter):
    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(round(value))


class FloatToIntTruncate(AttributeConverter):
    priority = 20
    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(value)
