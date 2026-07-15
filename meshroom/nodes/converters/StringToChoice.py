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
