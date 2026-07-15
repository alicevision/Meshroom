from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class IntToBool(AttributeConverter):
    srcType = desc.IntParam
    dstType = desc.BoolParam

    @classmethod
    def convert(cls, value):
        return bool(value)
