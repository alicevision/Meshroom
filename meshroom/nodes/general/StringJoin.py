__version__ = "1.0"

from meshroom.core import desc


class StringJoin(desc.Node):
    """ Join multiple strings using a given separator. """

    category = "Utils"

    inputs = [
        desc.ListAttribute(
            name="strings",
            description="Strings to join.",
            exposed=True,
            elementDesc=desc.StringParam(
                name="string",
                exposed=True,
                value="",
            )
        ),
        desc.StringParam(
            name="separator",
            description="Separator to join the strings with. If empty, no separator will be used.",
            value="",
        ),
        desc.GroupAttribute(
            name="spacesManagement",
            description="Option to manage spaces and new lines in input strings.",
            items=[
                desc.ChoiceParam(
                    name="newLinesManagement",
                    description="The new line characters will be processed before the whitespaces. "
                                "If new lines are replaced with whitespaces, these whitespaces will be replaced with the whitespace-related options.\n"
                                "- keep (default): No specific processing will be applied to new lines.\n"
                                "- trim: Anything after the first new line character will be removed.\n"
                                "- join: New line characters will be replaced with whitespaces.\n"
                                "- join_char: New line characters will be replaced with a specific provided character.",
                    values=["keep", "trim", "join", "join_char"],
                    value="keep"
                ),
                desc.StringParam(
                    name="newLineCharacter",
                    label="New Line Replacement Character",
                    description="Specific character that will replace the new line character for multiline input strings.",
                    value="",
                    enabled=lambda node: node.spacesManagement.newLinesManagement.value == "join_char",
                ),
                desc.BoolParam(
                    name="replaceWhitespaces",
                    description="If true, all the whitespaces in the input strings will be replaced with the provided replacement character.",
                    value=False,
                ),
                desc.StringParam(
                    name="replacementCharacter",
                    description="Character to replace the whitespaces in the input strings with. If empty, all the spaces will be removed.",
                    value="",
                    enabled=lambda node: node.spacesManagement.replaceWhitespaces.value,
                ),
            ]
        )
    ]

    outputs = [
        desc.StringParam(
            name="outputString",
            label="Joined String",
            description="Concatenation of all the inputs strings, separated with the provided character.",
            value=None,
        )
    ]

    def process(self, node):
        strings = []
        for s in node.strings.value:
            val = self._manageNewLines(node.spacesManagement.newLinesManagement.value,
                                       node.spacesManagement.newLineCharacter.value,
                                       s.value)

            if node.spacesManagement.replaceWhitespaces.value:
                val = val.replace(" ", node.spacesManagement.replacementCharacter.value)
            strings.append(val)

        separator = node.separator.value
        node.outputString.value = separator.join(strings)

    @staticmethod
    def _manageNewLines(policy, char, string):
        if policy == "trim":
            return string.split("\n", 1)[0]
        if policy == "join":
            return string.replace("\n", " ")
        if policy == "join_char":
            return string.replace("\n", char)
        return string
