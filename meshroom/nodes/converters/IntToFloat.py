from meshroom.core import desc


class IntToFloat(desc.AttributeConverter):
    srcType = desc.IntParam
    dstType = desc.FloatParam

    @classmethod
    def convert(cls, value):
        return float(value)
