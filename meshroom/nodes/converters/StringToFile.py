from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class StringToFile(AttributeConverter):
    srcType = desc.StringParam
    dstType = desc.File

    @classmethod
    def convert(cls, value):
        return str(value)
