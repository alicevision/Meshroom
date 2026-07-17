from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class BoolToInt(AttributeConverter):
    srcType = desc.BoolParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(bool(value))
