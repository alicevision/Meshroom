#!/usr/bin/env python
# coding:utf-8

from meshroom.core.graph import Graph, loadGraph, executeGraph
from meshroom.core import desc, pluginManager
from meshroom.core.node import Node
from meshroom.core.plugins import NodePlugin


class NodeWithAttributesNeedingFormatting(desc.Node):
    """
    A node containing list, file, choice and group attributes in order to test the
    formatting of the command line.
    """
    inputs = [
        desc.ListAttribute(
            name="images",
            label="Images",
            description="List of images.",
            elementDesc=desc.File(
                name="image",
                label="Image",
                description="Path to an image.",
                value="",
            ),
        ),
        desc.File(
            name="input",
            label="Input File",
            description="An input file.",
            value="",
        ),
        desc.ChoiceParam(
            name="method",
            label="Method",
            description="Method to choose from a list of available methods.",
            value="MethodC",
            values=["MethodA", "MethodB", "MethodC"],
        ),
        desc.GroupAttribute(
            name="firstGroup",
            label="First Group",
            description="Group with boolean and integer parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="enableFirstGroup",
                    label="Enable",
                    description="Enable other parameter in the group.",
                    value=False,
                ),
                desc.IntParam(
                    name="width",
                    label="Width",
                    description="Width setting.",
                    value=3,
                    range=(1, 10, 1),
                    enabled=lambda node: node.firstGroup.enableFirstGroup.value,
                ),
            ]
        ),
        desc.GroupAttribute(
            name="secondGroup",
            label="Second Group",
            description="Group with boolean, choice and float parameters.",
            joinChar=",",
            groupDesc=[
                desc.BoolParam(
                    name="enableSecondGroup",
                    label="Enable",
                    description="Enable other parameters in the group.",
                    value=False,
                ),
                desc.ChoiceParam(
                    name="groupChoice",
                    label="Grouped Choice",
                    description="Value to choose from a group.",
                    value="second_value",
                    values=["first_value", "second_value", "third_value"],
                    enabled=lambda node: node.secondGroup.enableSecondGroup.value,
                ),
                desc.FloatParam(
                    name="floatWidth",
                    label="Width",
                    description="Width setting (but with a float).",
                    value=3.0,
                    range=(1.0, 10.0, 0.5),
                    enabled=lambda node: node.secondGroup.enableSecondGroup.value,
                ),
            ],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output file.",
            value="{nodeCacheFolder}",
        ),
    ]

class TestCommandLineFormatting:
    nodePlugin = NodePlugin(NodeWithAttributesNeedingFormatting)

    @classmethod
    def setup_class(cls):
        pluginManager.registerNode(cls.nodePlugin)

    @classmethod
    def teardown_class(cls):
        pluginManager.unregisterNode(cls.nodePlugin)

    def test_formatting_listOfFiles(self):
        inputImages = ["/non/existing/fileA", "/non/existing/with space/fileB"]

        graph = Graph("")
        node = graph.addNewNode("NodeWithAttributesNeedingFormatting")

        # Assert that an empty list gives an empty string
        assert node.images.getValueStr() == ""

        # Assert that values in a list a correctly concatenated
        node.images.extend([i for i in inputImages])
        assert node.images.getValueStr() == '"/non/existing/fileA" "/non/existing/with space/fileB"'

        # Reset list content and add a single value that contains spaces
        node.images.resetToDefaultValue()
        assert node.images.getValueStr() == ""  # The value has been correctly reset
        node.images.extend("single value with space")
        assert node.images.getValueStr() == '"single value with space"'

        # Assert that extending values when the list is not empty is working
        node.images.extend(inputImages)
        assert node.images.getValueStr() == \
            '"single value with space" "{}" "{}"'.format(inputImages[0],
                                                         inputImages[1])

        # Values are not retrieved as strings in the command line, so quotes around them are
        # not expected
        assert node._cmdVars["imagesValue"] == \
            'single value with space {} {}'.format(inputImages[0],
                                                   inputImages[1])

    def test_formatting_strings(self):
        graph = Graph("")
        node = graph.addNewNode("NodeWithAttributesNeedingFormatting")
        node._buildCmdVars()

        # Assert an empty File attribute generates empty quotes when requesting its value as
        # a string
        assert node.input.getValueStr() == '""'
        assert node._cmdVars["inputValue"] == ""

        # Assert a Choice attribute with a non-empty default value is surrounded with quotes
        # when requested as a string
        assert node.method.getValueStr() == '"MethodC"'
        assert node._cmdVars["methodValue"] == "MethodC"

        # Assert that the empty list is really empty (no quotes)
        assert node.images.getValueStr() == ""
        assert node._cmdVars["imagesValue"] == "", "Empty list should become fully empty"

        # Assert that the list with one empty value generates empty quotes
        node.images.extend("")
        assert node.images.getValueStr() == '""', \
            "A list with one empty string should generate empty quotes"
        assert node._cmdVars["imagesValue"] == "", \
            "The value is always only the value, so empty here"

        # Assert that a list with 2 empty strings generates quotes
        node.images.extend("")
        assert node.images.getValueStr() == '"" ""', \
            "A list with 2 empty strings should generate quotes"
        assert node._cmdVars["imagesValue"] == ' ', \
            "The value is always only the value, so 2 empty strings with the " \
            "space separator in the middle"

    def test_formatting_groups(self):
        graph = Graph("")
        node = graph.addNewNode("NodeWithAttributesNeedingFormatting")
        node._buildCmdVars()

        assert node.firstGroup.getValueStr() == '"False:3"'
        assert node._cmdVars["firstGroupValue"] == 'False:3', \
            "There should be no quotes here as the value is not formatted as a string"

        assert node.secondGroup.getValueStr() == '"False,second_value,3.0"'
        assert node._cmdVars["secondGroupValue"] == 'False,second_value,3.0'
