#!/usr/bin/env python
# coding:utf-8

from meshroom.core.graph import Graph
from meshroom.core import desc

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithCommandLineFormatting_usingNode(desc.CommandLineNode):
    """
    A node using a lambda for the commandLine member variable.
    """
    commandLine = "myapp --input {node.input.value} --output {node.output.value}"

    inputs = [
        desc.File(
            name="input",
            label="Input File",
            description="An input file.",
            value="/some/input",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output file.",
            value="output.txt",
        ),
    ]


class NodeWithCommandLineFormatting_usingValue(desc.CommandLineNode):
    """
    A node using a string template for the commandLine member variable.
    """
    commandLine = "myapp --input {inputValue} --output {outputValue}"

    inputs = [
        desc.File(
            name="input",
            label="Input File",
            description="An input file.",
            value="/some/input",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output file.",
            value="output.txt",
        ),
    ]


class TestCommandLineFormatting:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithCommandLineFormatting_usingNode)
        registerNodeDesc(NodeWithCommandLineFormatting_usingValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingNode)
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingValue)

    def test_commandLine_node(self):
        graph = Graph("")
        nodeN = graph.addNewNode("NodeWithCommandLineFormatting_usingNode")
        nodeV = graph.addNewNode("NodeWithCommandLineFormatting_usingValue")

        nodeN.input.value = "/path/in"
        nodeV.input.value = "/path/in"
        nodeN._buildExpVars()  # populate _expVars
        nodeV._buildExpVars()  # populate _expVars

        cmdN = nodeN.nodeDesc.buildCommandLine(nodeN.chunks[0])
        cmdV = nodeV.nodeDesc.buildCommandLine(nodeV.chunks[0])
        assert cmdN
        assert cmdV
        assert cmdN == cmdV

