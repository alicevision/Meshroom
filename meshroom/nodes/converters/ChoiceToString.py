from meshroom.core import desc


class ChoiceToString(desc.AttributeConverter):
    srcType = desc.ChoiceParam
    dstType = desc.StringParam

    @classmethod
    def convert(cls, value):
        return str(value)
