#!/usr/bin/env python
# coding:utf-8
import meshroom.multiview


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

    assert graph1.findNode('CameraInit').viewpoints[0].path.value == '/non/existing/fileA'
    assert len(graph2.findNode('CameraInit').viewpoints) == 0
    assert graph3.findNode('CameraInit').viewpoints[0].path.value == '/non/existing/file1'
    assert graph4.findNode('CameraInit').viewpoints[0].path.value == '/non/existing/file1'

    assert len(graph1.findNode('CameraInit').viewpoints) == 1
    assert len(graph2.findNode('CameraInit').viewpoints) == 0
    assert len(graph3.findNode('CameraInit').viewpoints) == 2
    assert len(graph4.findNode('CameraInit').viewpoints) == 2

    viewpoints = graph3.findNode('CameraInit').viewpoints
    assert viewpoints[0].path.value == '/non/existing/file1'

    assert viewpoints[0].path.value == '/non/existing/file1'
    assert viewpoints[0].intrinsicId.value == -1
    assert viewpoints[1].path.value == '/non/existing/file2'
    assert viewpoints[1].intrinsicId.value == -1

    assert viewpoints[0].path.isDefault() == False
    assert viewpoints[0].intrinsicId.isDefault() == True
    assert viewpoints.getPrimitiveValue(exportDefault=False) == [
        {"path": '/non/existing/file1'},
        {"path": '/non/existing/file2'},
    ]

    for graph in (graph4, graph4b):
        viewpoints = graph.findNode('CameraInit').viewpoints
        assert viewpoints[0].path.value == '/non/existing/file1'
        assert viewpoints[0].intrinsicId.value == 50
        assert viewpoints[1].path.value == '/non/existing/file2'
        assert viewpoints[1].intrinsicId.value == 55

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

