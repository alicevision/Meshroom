#!/usr/bin/env python
# coding:utf-8
import os
import tempfile

import meshroom.multiview
from meshroom.core.graph import loadGraph
from meshroom.core.node import Node


def test_multiviewPipeline():
    graph1 = meshroom.multiview.photogrammetry(inputImages=['/non/existing/fileA'])
    graph2 = meshroom.multiview.photogrammetry(inputImages=[])
    graph2b = meshroom.multiview.photogrammetry(inputImages=[])
    graph3 = meshroom.multiview.photogrammetry(inputImages=['/non/existing/file1', '/non/existing/file2'])
    graph4 = meshroom.multiview.photogrammetry(inputViewpoints=[
        {'path': '/non/existing/file1', 'intrinsicId': 50},
        {'path': '/non/existing/file2', 'intrinsicId': 55}
        ])
    graph4b = meshroom.multiview.photogrammetry(inputViewpoints=[
        {'path': '/non/existing/file1', 'intrinsicId': 50},
        {'path': '/non/existing/file2', 'intrinsicId': 55}
        ])

    assert graph1.findNode('CameraInit').viewpoints.at(0).path.value == '/non/existing/fileA'
    assert len(graph2.findNode('CameraInit').viewpoints) == 0
    assert graph3.findNode('CameraInit').viewpoints.at(0).path.value == '/non/existing/file1'
    assert graph4.findNode('CameraInit').viewpoints.at(0).path.value == '/non/existing/file1'

    assert len(graph1.findNode('CameraInit').viewpoints) == 1
    assert len(graph2.findNode('CameraInit').viewpoints) == 0
    assert len(graph3.findNode('CameraInit').viewpoints) == 2
    assert len(graph4.findNode('CameraInit').viewpoints) == 2

    viewpoints = graph3.findNode('CameraInit').viewpoints
    assert viewpoints.at(0).path.value == '/non/existing/file1'

    assert viewpoints.at(0).path.value == '/non/existing/file1'
    assert viewpoints.at(0).intrinsicId.value == -1
    assert viewpoints.at(1).path.value == '/non/existing/file2'
    assert viewpoints.at(1).intrinsicId.value == -1

    assert not viewpoints.at(0).path.isDefault
    assert viewpoints.at(0).intrinsicId.isDefault
    assert viewpoints.getPrimitiveValue(exportDefault=False) == [
        {"path": '/non/existing/file1'},
        {"path": '/non/existing/file2'},
    ]

    for graph in (graph4, graph4b):
        viewpoints = graph.findNode('CameraInit').viewpoints
        assert viewpoints.at(0).path.value == '/non/existing/file1'
        assert viewpoints.at(0).intrinsicId.value == 50
        assert viewpoints.at(1).path.value == '/non/existing/file2'
        assert viewpoints.at(1).intrinsicId.value == 55

    # Ensure that all output UIDs are different as the input is different:
    # graph1 != graph2 != graph3 != graph4
    for otherGraph in (graph2, graph3, graph4):
        for node in graph1.nodes:
            otherNode = otherGraph.node(node.name)
            for key, attr in node.attributes.items():
                if attr.isOutput:
                    otherAttr = otherNode.attribute(key)
                    assert attr.uid() != otherAttr.uid()

    # graph2 == graph2b
    nodes, edges = graph2.dfsOnFinish()
    for node in nodes:
        otherNode = graph2b.node(node.name)
        for key, attr in node.attributes.items():
            otherAttr = otherNode.attribute(key)
            if attr.isOutput:
                assert attr.uid() == otherAttr.uid()
            else:
                for uidIndex in attr.desc.uid:
                    assert attr.uid(uidIndex) == otherAttr.uid(uidIndex)

    # graph4 == graph4b
    nodes, edges = graph4.dfsOnFinish()
    for node in nodes:
        otherNode = graph4b.node(node.name)
        for key, attr in node.attributes.items():
            otherAttr = otherNode.attribute(key)
            if attr.isOutput:
                assert attr.uid() == otherAttr.uid()
            else:
                for uidIndex in attr.desc.uid:
                    assert attr.uid(uidIndex) == otherAttr.uid(uidIndex)

    # test serialization/deserialization
    for graph in [graph1, graph2, graph3, graph4]:
        filename = tempfile.mktemp()
        graph.save(filename)
        loadedGraph = loadGraph(filename)
        os.remove(filename)
        # check that all nodes have been properly de-serialized
        #  - same node set
        assert sorted([n.name for n in loadedGraph.nodes]) == sorted([n.name for n in graph.nodes])
        #  - no compatibility issues
        assert all(isinstance(n, Node) for n in loadedGraph.nodes)
