import os
import fnmatch
import re

from .core.graph import Graph, GraphModification


def findFiles(folder, patterns):
    rules = [re.compile(fnmatch.translate(pattern), re.IGNORECASE) for pattern in patterns]
    outFiles = []
    for name in os.listdir(folder):
        for rule in rules:
            if rule.match(name):
                filepath = os.path.join(folder, name)
                outFiles.append(filepath)
                break
    return outFiles


def photogrammetryPipeline(output='', inputFolder='', inputImages=[], inputViewpoints=[]):
    # type: () -> Graph
    graph = Graph('pipeline')
    with GraphModification(graph):
        cameraInit = graph.addNewNode('CameraInit')
        if inputFolder:
            images = findFiles(inputFolder, ['*.jpg', '*.png'])
            cameraInit.viewpoints.extend([{'path': image} for image in images])
        if inputImages:
            cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        if inputViewpoints:
            cameraInit.viewpoints.extend(inputViewpoints)
        featureExtraction = graph.addNewNode('FeatureExtraction',
                                             input=cameraInit.output)
        imageMatching = graph.addNewNode('ImageMatching',
                                             input=featureExtraction.input,
                                             featuresFolder=featureExtraction.output,
                                             )
        featureMatching = graph.addNewNode('FeatureMatching',
                                           input=imageMatching.input,
                                           featuresFolder=imageMatching.featuresFolder,
                                           imagePairsList=imageMatching.output)
        structureFromMotion = graph.addNewNode('StructureFromMotion',
                                               input=featureMatching.input,
                                               featuresFolder=featureMatching.featuresFolder,
                                               matchesFolder=featureMatching.output)
        prepareDenseScene = graph.addNewNode('PrepareDenseScene',
                                             input=structureFromMotion.output)
        cameraConnection = graph.addNewNode('CameraConnection',
                                    ini=prepareDenseScene.ini)
        depthMap = graph.addNewNode('DepthMap',
                                    ini=cameraConnection.ini)
        depthMapFilter = graph.addNewNode('DepthMapFilter',
                                          depthMapFolder=depthMap.output,
                                          ini=depthMap.ini)
        meshing = graph.addNewNode('Meshing',
                                   depthMapFolder=depthMapFilter.depthMapFolder,
                                   depthMapFilterFolder=depthMapFilter.output,
                                   ini=depthMapFilter.ini)
        texturing = graph.addNewNode('Texturing',
                                     ini=meshing.ini,
                                     inputDenseReconstruction=meshing.outputDenseReconstruction)
    return graph

