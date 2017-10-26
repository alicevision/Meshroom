import os

from .core.graph import Graph


def photogrammetryPipeline():
    # type: () -> Graph
    graph = Graph('pipeline')
    cameraInit = graph.addNewNode('CameraInit')
    featureExtraction = graph.addNewNode('FeatureExtraction',
                                         input=cameraInit.outputSfm)
    imageMatching = graph.addNewNode('ImageMatching',
                                         input=cameraInit.outputSfm,
                                         featuresDirectory=featureExtraction.output,
                                         )
    featureMatching = graph.addNewNode('FeatureMatching',
                                       input=cameraInit.outputSfm,
                                       featuresDirectory=featureExtraction.output,
                                       imagePairsList=imageMatching.output)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=cameraInit.outputSfm,
                                           featuresDirectory=featureExtraction.output,
                                           matchesDirectory=featureMatching.output)
    prepareDenseScene = graph.addNewNode('PrepareDenseScene',
                                         input=structureFromMotion.output)
    camPairs = graph.addNewNode('CamPairs',
                                mvsConfig=prepareDenseScene.mvsConfig)
    depthMap = graph.addNewNode('DepthMap',
                                mvsConfig=camPairs.mvsConfig)
    depthMapFilter = graph.addNewNode('DepthMapFilter',
                                      mvsConfig=depthMap.mvsConfig)
    meshing = graph.addNewNode('Meshing',
                               mvsConfig=depthMapFilter.mvsConfig)
    texturing = graph.addNewNode('Texturing',
                                 mvsConfig=meshing.mvsConfig)
    return graph


