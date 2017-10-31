#!/usr/bin/env python
# coding:utf-8
import meshroom.multiview


def test_multiviewPipeline():
    graph1 = meshroom.multiview.photogrammetryPipeline(inputFolder='/non/existing/folder')
    graph2 = meshroom.multiview.photogrammetryPipeline(inputImages=[])
    graph3 = meshroom.multiview.photogrammetryPipeline(inputImages=['/non/existing/file1', '/non/existing/file2'])
    graph4 = meshroom.multiview.photogrammetryPipeline(inputViewpoints=[
        {'image': '/non/existing/file1', 'focal': 50},
        {'image': '/non/existing/file2', 'focal': 55}
        ])

    assert graph1.findNode('CameraInit').imageDirectory.value == '/non/existing/folder'
    assert graph2.findNode('CameraInit').imageDirectory.value == ''
    assert graph3.findNode('CameraInit').imageDirectory.value == ''
    assert graph4.findNode('CameraInit').imageDirectory.value == ''

    assert len(graph1.findNode('CameraInit').viewpoints) == 0
    assert len(graph2.findNode('CameraInit').viewpoints) == 0
    assert len(graph3.findNode('CameraInit').viewpoints) == 2
    assert len(graph4.findNode('CameraInit').viewpoints) == 2

    viewpoints = graph3.findNode('CameraInit').viewpoints
    assert viewpoints[0].image.value == '/non/existing/file1'
    assert viewpoints[0].focal.value == -1
    assert viewpoints[1].image.value == '/non/existing/file2'
    assert viewpoints[1].focal.value == -1

    viewpoints = graph4.findNode('CameraInit').viewpoints
    assert viewpoints[0].image.value == '/non/existing/file1'
    assert viewpoints[0].focal.value == 50
    assert viewpoints[1].image.value == '/non/existing/file2'
    assert viewpoints[1].focal.value == 55
