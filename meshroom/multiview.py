import os

from .core.graph import Graph


def photogrammetryPipeline(inputFolder='', inputImages=[], inputViewpoints=[]):
    # type: () -> Graph
    graph = Graph('pipeline')
    cameraInit = graph.addNewNode('CameraInit', imageDirectory=inputFolder)
    cameraInit.viewpoints.value = [{'image': image, 'focal': -1} for image in inputImages]
    cameraInit.viewpoints.extend(inputViewpoints)
    featureExtraction = graph.addNewNode('FeatureExtraction',
                                         input=cameraInit.outputSfm)
    imageMatching = graph.addNewNode('ImageMatching',
                                         input=featureExtraction.input,
                                         featuresDirectory=featureExtraction.output,
                                         )
    featureMatching = graph.addNewNode('FeatureMatching',
                                       input=imageMatching.input,
                                       featuresDirectory=imageMatching.featuresDirectory,
                                       imagePairsList=imageMatching.output)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=featureMatching.input,
                                           featuresDirectory=featureMatching.featuresDirectory,
                                           matchesDirectory=featureMatching.output)
    prepareDenseScene = graph.addNewNode('PrepareDenseScene',
                                         input=structureFromMotion.output)
    cameraConnection = graph.addNewNode('CameraConnection',
                                ini=prepareDenseScene.ini)
    depthMap = graph.addNewNode('DepthMap',
                                ini=cameraConnection.ini)
    depthMapFilter = graph.addNewNode('DepthMapFilter',
                                      ini=depthMap.ini)
    meshing = graph.addNewNode('Meshing',
                               ini=depthMapFilter.ini)
    texturing = graph.addNewNode('Texturing',
                                 ini=meshing.ini)
    return graph


