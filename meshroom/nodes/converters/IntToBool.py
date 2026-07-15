from meshroom.core import desc


class IntToBool(desc.AttributeConverter):
    srcType = desc.IntParam
    dstType = desc.BoolParam

    @classmethod
    def convert(cls, value):
        return bool(value)
