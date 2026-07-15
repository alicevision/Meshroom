from meshroom.core import desc


class StringToFile(desc.AttributeConverter):
    srcType = desc.StringParam
    dstType = desc.File

    @classmethod
    def convert(cls, value):
        return str(value)
