from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class FileToString(AttributeConverter):
    srcType = desc.File
    dstType = desc.StringParam

    @classmethod
    def convert(cls, value):
        return str(value) if value is not None else ""
