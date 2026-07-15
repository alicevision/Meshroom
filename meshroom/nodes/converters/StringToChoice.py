from meshroom.core import desc
from meshroom.core.attributeConverter import AttributeConverter


class StringToChoice(AttributeConverter):
    description = (
        "Convert a StringParam to a ChoiceParam."
    )
    
    priority = 20
    srcType = desc.StringParam
    dstType = desc.ChoiceParam

    @classmethod
    def convert(cls, value):
        return str(value)


class StringToChoiceStrict(AttributeConverter):
    """
    StringToChoice with enforcement that the converted 
    value is included in the destination values.
    """
    
    description = (
        "Convert a StringParam to a ChoiceParam "
        "if the value is already included in the "
        "possible values."
    )

    srcType = desc.StringParam
    dstType = desc.ChoiceParam

    @classmethod
    def convert(cls, value):
        return str(value)

    @classmethod
    def isValid(cls, srcAttr, dstAttr):
        values = dstAttr.desc.values
        if callable(values):
            values = values(dstAttr.node) if hasattr(dstAttr, "node") else values
        return values is None or srcAttr.value in values
