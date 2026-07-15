from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class ChoiceToString(AttributeConverter):
    srcType = desc.ChoiceParam
    dstType = desc.StringParam

    @classmethod
    def convert(cls, value):
        return str(value)
