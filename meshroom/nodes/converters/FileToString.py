from meshroom.core import desc


class FileToString(desc.AttributeConverter):
    srcType = desc.File
    dstType = desc.StringParam

    @classmethod
    def convert(cls, value):
        return str(value) if value is not None else ""
