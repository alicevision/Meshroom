#!/usr/bin/env python
# coding:utf-8

from meshroom.core.graph import Graph
from meshroom.core import desc

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithCommandLineFormatting_usingNodeAndLambda(desc.CommandLineNode):
    """
    A node using a lambda for the commandLine member variable.
    """
    commandLine = lambda node: f"myapp --input {node.input.value} --output {node.output.value}"

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

def customFunction_commandline(node):
    return f"myapp --input {node.input.value} --output {node.output.value}"


class NodeWithCommandLineFormatting_usingNodeAndFunction(desc.CommandLineNode):
    """
    A node using a function for the commandLine member variable.
    """
    commandLine = customFunction_commandline

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
        registerNodeDesc(NodeWithCommandLineFormatting_usingNodeAndLambda)
        registerNodeDesc(NodeWithCommandLineFormatting_usingNodeAndFunction)
        registerNodeDesc(NodeWithCommandLineFormatting_usingNode)
        registerNodeDesc(NodeWithCommandLineFormatting_usingValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingNodeAndLambda)
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingNodeAndFunction)
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingNode)
        unregisterNodeDesc(NodeWithCommandLineFormatting_usingValue)

    def test_commandLine_node(self):
        graph = Graph("")
        nodeNL = graph.addNewNode("NodeWithCommandLineFormatting_usingNodeAndLambda")
        nodeNF = graph.addNewNode("NodeWithCommandLineFormatting_usingNodeAndFunction")
        nodeN = graph.addNewNode("NodeWithCommandLineFormatting_usingNode")
        nodeV = graph.addNewNode("NodeWithCommandLineFormatting_usingValue")

        nodeNL.input.value = "/path/in"
        nodeNF.input.value = "/path/in"
        nodeN.input.value = "/path/in"
        nodeV.input.value = "/path/in"

        nodeNL._buildExpVars()  # populate _expVars
        nodeNF._buildExpVars()  # populate _expVars
        nodeN._buildExpVars()  # populate _expVars
        nodeV._buildExpVars()  # populate _expVars

        cmdNL = nodeNL.nodeDesc.buildCommandLine(nodeNL.chunks[0])
        cmdNF = nodeNL.nodeDesc.buildCommandLine(nodeNF.chunks[0])
        cmdN = nodeN.nodeDesc.buildCommandLine(nodeN.chunks[0])
        cmdV = nodeV.nodeDesc.buildCommandLine(nodeV.chunks[0])

        assert cmdNL
        assert cmdNF
        assert cmdN
        assert cmdV

        assert cmdNL == cmdNF
        assert cmdN == cmdNL
        assert cmdN == cmdV

