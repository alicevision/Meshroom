#!/usr/bin/env python
# coding:utf-8
import os
import tempfile

import meshroom.multiview
from meshroom.core.graph import loadGraph
from meshroom.core.node import Node


def test_pipeline():
    meshroom.core.initNodes()
    meshroom.core.initPipelines()

    graph1InputFiles = ["/non/existing/file1", "/non/existing/file2"]
    graph1 = loadGraph(meshroom.core.pipelineTemplates["appendTextAndFiles"])
    graph1.name = "graph1"
    graph1AppendText1 = graph1.node("AppendText_1")
    graph1AppendText1.input.value = graph1InputFiles[0]
    graph1AppendText2 = graph1.node("AppendText_2")
    graph1AppendText2.input.value = graph1InputFiles[1]

    assert graph1.findNode("AppendFiles").input.value == graph1AppendText1.output.value
    assert graph1.findNode("AppendFiles").input2.value == graph1AppendText2.output.value
    assert graph1.findNode("AppendFiles").input3.value == graph1InputFiles[0]
    assert graph1.findNode("AppendFiles").input4.value == graph1InputFiles[1]

    assert not graph1AppendText1.input.isDefault
    assert graph1AppendText2.input.getPrimitiveValue() == graph1InputFiles[1]

    graph2InputFiles = ["/non/existing/file", ""]
    graph2 = loadGraph(meshroom.core.pipelineTemplates["appendTextAndFiles"])
    graph2.name = "graph2"
    graph2AppendText1 = graph2.node("AppendText_1")
    graph2AppendText1.input.value = graph2InputFiles[0]
    graph2AppendText2 = graph2.node("AppendText_2")
    graph2AppendText2.input.value = graph2InputFiles[1]

    # Ensure that all output UIDs are different as the input is different:
    # graph1 != graph2
    for node in graph1.nodes:
        otherNode = graph2.node(node.name)
        for key, attr in node.attributes.items():
            if attr.isOutput and attr.enabled:
                otherAttr = otherNode.attribute(key)
                assert attr.uid() != otherAttr.uid()

    # Test serialization/deserialization on both graphs
    for graph in [graph1, graph2]:
        filename = tempfile.mktemp()
        graph.save(filename)
        loadedGraph = loadGraph(filename)
        os.remove(filename)
        # Check that all nodes have been properly de-serialized
        #  - Same node set
        assert sorted([n.name for n in loadedGraph.nodes]) == sorted([n.name for n in graph.nodes])
        #  - No compatibility issues
        assert all(isinstance(n, Node) for n in loadedGraph.nodes)
        #  - Same UIDs for every node
        assert sorted([n._uid for n in loadedGraph.nodes]) == sorted([n._uid for n in graph.nodes])

    # Graph 2b, set with identical parameters as graph 2
    graph2b = loadGraph(meshroom.core.pipelineTemplates["appendTextAndFiles"])
    graph2b.name = "graph2b"
    graph2bAppendText1 = graph2b.node("AppendText_1")
    graph2bAppendText1.input.value = graph2InputFiles[0]
    graph2bAppendText2 = graph2b.node("AppendText_2")
    graph2bAppendText2.input.value = graph2InputFiles[1]

    # Ensure that graph2 == graph2b
    nodes, edges = graph2.dfsOnFinish()
    for node in nodes:
        otherNode = graph2b.node(node.name)
        for key, attr in node.attributes.items():
            otherAttr = otherNode.attribute(key)
            if attr.isOutput and attr.enabled:
                assert attr.uid() == otherAttr.uid()
            else:
                assert attr.uid() == otherAttr.uid()
