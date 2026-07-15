from meshroom.core import desc


class FloatToIntRound(desc.AttributeConverter):
    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(round(value))


class FloatToIntTruncate(desc.AttributeConverter):
    priority = 20
    srcType = desc.FloatParam
    dstType = desc.IntParam

    @classmethod
    def convert(cls, value):
        return int(value)
