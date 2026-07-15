from meshroom.core import desc


class IntToBool(desc.AttributeConverter):
    srcType = desc.BoolParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(bool(value))
