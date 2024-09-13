#!/usr/bin/env python
# coding:utf-8
import meshroom.multiview
from meshroom.core.graph import Graph


def test_formatting_listOfFiles():
    meshroom.core.initNodes()

    inputImages = ['/non/existing/fileA', '/non/existing/with space/fileB']

    graph = Graph('')
    n1 = graph.addNewNode('CameraInit')
    n1.viewpoints.extend([{'path': image} for image in inputImages])
    # viewId, poseId, path, intrinsicId, rigId, subPoseId, metadata
    assert n1.viewpoints.getValueStr() == \
        '-1 -1 "/non/existing/fileA" -1 -1 -1 "" -1 -1 "/non/existing/with space/fileB" -1 -1 -1 ""'

    graph = Graph('')
    n1 = graph.addNewNode('ImageMatching')
    assert n1.featuresFolders.getValueStr() == ''

    n1.featuresFolders.extend("single value with space")
    assert n1.featuresFolders.getValueStr() == '"single value with space"'

    n1.featuresFolders.resetToDefaultValue()
    assert n1.featuresFolders.getValueStr() == ''

    n1.featuresFolders.extend(inputImages)
    assert n1.featuresFolders.getValueStr() == '"/non/existing/fileA" "/non/existing/with space/fileB"'

    n1._buildCmdVars()  # prepare vars for command line creation
    # and check some values
    name = 'featuresFolders'
    assert n1._cmdVars[name + 'Value'] == '/non/existing/fileA /non/existing/with space/fileB'


def test_formatting_strings():
    meshroom.core.initNodes()

    graph = Graph('')
    n1 = graph.addNewNode('ImageMatching')
    name = 'weights'
    assert n1.weights.getValueStr() == '""'  # Empty string should generate empty quotes
    assert n1._cmdVars[name + 'Value'] == ''
    name = 'method'
    assert n1.method.getValueStr() == '"SequentialAndVocabularyTree"'
    assert n1._cmdVars[name + 'Value'] == 'SequentialAndVocabularyTree'

    n2 = graph.addNewNode('ImageMatching')
    n2._buildCmdVars()  # prepare vars for command line creation
    name = 'featuresFolders'
    assert n2._cmdVars[name + 'Value'] == '', 'Empty list should become fully empty'
    n2.featuresFolders.extend('')
    n2._buildCmdVars()  # prepare vars for command line creation
    assert n2.featuresFolders.getValueStr() == '""', 'A list with one empty string should generate empty quotes'
    assert n2._cmdVars[name + 'Value'] == '', 'The Value is always only the value, so empty here'
    n2.featuresFolders.extend('')
    n2._buildCmdVars()  # prepare vars for command line creation
    assert n2.featuresFolders.getValueStr() == '"" ""', 'A list with 2 empty strings should generate quotes'
    assert n2._cmdVars[name + 'Value'] == ' ', \
        'The Value is always only the value, so 2 empty with the space separator in the middle'


def test_formatting_groups():
    meshroom.core.initNodes()

    graph = Graph('')
    n3 = graph.addNewNode('ImageProcessing')
    n3._buildCmdVars()  # prepare vars for command line creation
    name = 'sharpenFilter'
    assert n3.sharpenFilter.getValueStr() == '"False:3:1.0:0.0"'
    assert n3._cmdVars[name + 'Value'] == 'False:3:1.0:0.0', 'The Value is always only the value, so no quotes'
    name = 'fillHoles'
    assert n3._cmdVars[name + 'Value'] == 'False', 'Booleans'
    name = 'noiseFilter'
    assert n3.noiseFilter.getValueStr() == '"False:uniform:0.0:1.0:True"'
    assert n3._cmdVars[name + 'Value'] == 'False:uniform:0.0:1.0:True'
