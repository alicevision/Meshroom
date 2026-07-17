from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class IntToFloat(AttributeConverter):
    srcType = desc.IntParam
    dstType = desc.FloatParam

    @classmethod
    def convert(cls, value):
        return float(value)
