#!/usr/bin/env python
# coding:utf-8
import os
import tempfile

import meshroom.multiview
from meshroom.core.graph import Graph
from meshroom.core.node import Node


def test_formatting_listOfFiles():
    inputImages = ['/non/existing/fileA', '/non/existing/with space/fileB']

    graph = Graph('')
    n1 = graph.addNewNode('CameraInit')
    n1.viewpoints.extend([{'path': image} for image in inputImages])
    # viewId, poseId, path, intrinsicId, rigId, subPoseId, metadata
    assert n1.viewpoints.getValueStr() == '-1 -1 "/non/existing/fileA" -1 -1 -1 "" -1 -1 "/non/existing/with space/fileB" -1 -1 -1 ""'

    assert n1.allowedCameraModels.getValueStr() == '"pinhole,radial1,radial3,brown,fisheye4,fisheye1,3deanamorphic4,3deradial4,3declassicld"'

    graph = Graph('')
    n1 = graph.addNewNode('ImageMatching')
    assert n1.featuresFolders.getValueStr() == ''

    n1.featuresFolders.extend("single value with space")
    assert n1.featuresFolders.getValueStr() == '"single value with space"'

    n1.featuresFolders.resetValue()
    assert n1.featuresFolders.getValueStr() == ''

    value = '"/non/existing/fileA" "/non/existing/with space/fileB"'
    n1.featuresFolders.extend(inputImages)
    assert n1.featuresFolders.getValueStr() == value

    n1._buildCmdVars()  # prepare vars for command line creation
    # and check some values
    name = 'featuresFolders'
    assert n1._cmdVars[name + 'Value'] == value


def test_formatting_strings():
    graph = Graph('')
    n1 = graph.addNewNode('ImageMatching')
    name = 'weights'
    assert n1._cmdVars[name + 'Value'] == '""'  # Empty string should generate empty quotes
    name = 'method'
    assert n1._cmdVars[name + 'Value'] == '"SequentialAndVocabularyTree"'

    n2 = graph.addNewNode('ImageMatching')
    n2._buildCmdVars()  # prepare vars for command line creation
    name = 'featuresFolders'
    assert n2._cmdVars[name + 'Value'] == ''  # Empty list should become fully empty
    n2.featuresFolders.extend('')
    n2._buildCmdVars()  # prepare vars for command line creation
    assert n2._cmdVars[name + 'Value'] == '""'  # A list with one empty string should generate empty quotes
    n2.featuresFolders.extend('')
    n2._buildCmdVars()  # prepare vars for command line creation
    assert n2._cmdVars[name + 'Value'] == '"" ""'  # A list with 2 empty strings should generate quotes


def test_formatting_groups():
    graph = Graph('')
    n3 = graph.addNewNode('ImageProcessing')
    n3._buildCmdVars()  # prepare vars for command line creation
    name = 'sharpenFilter'
    assert n3._cmdVars[name + 'Value'] == 'False:3:1.0:0.0'
    name = 'fillHoles'
    assert n3._cmdVars[name + 'Value'] == 'False'  # Booleans
    name = 'noiseFilter'
    assert n3._cmdVars[name + 'Value'] == 'False:"uniform":0.0:1.0:True'

