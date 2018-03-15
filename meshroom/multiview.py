import os
import fnmatch
import re

from meshroom.core.graph import Graph, GraphModification


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


def photogrammetry(inputFolder='', inputImages=(), inputViewpoints=(), output=''):
    """
    Create a new Graph with a complete photogrammetry pipeline.

    Args:
        inputFolder (str, optional): folder containing image files
        inputImages (list of str, optional): list of image file paths
        inputViewpoints (list of Viewpoint, optional): list of Viewpoints
        output (str, optional): the path to export reconstructed model to

    Returns:
        Graph: the created graph
    """
    graph = Graph('Photogrammetry')
    with GraphModification(graph):
        sfmNodes, mvsNodes = photogrammetryPipeline(graph)
        cameraInit = sfmNodes[0]
        if inputFolder:
            images = findFiles(inputFolder, ['*.jpg', '*.png'])
            cameraInit.viewpoints.extend([{'path': image} for image in images])
        if inputImages:
            cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        if inputViewpoints:
            cameraInit.viewpoints.extend(inputViewpoints)

    if output:
        texturing = mvsNodes[-1]
        graph.addNewNode('Publish', output=output, inputFiles=[texturing.outputMesh,
                                                               texturing.outputMaterial,
                                                               texturing.outputTextures])
    return graph


def photogrammetryPipeline(graph):
    """
    Instantiate a complete photogrammetry pipeline inside 'graph'.

    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated

    Returns:
        list of Node: the created nodes
    """
    sfmNodes = sfmPipeline(graph)
    mvsNodes = mvsPipeline(graph, sfmNodes[-1])

    return sfmNodes, mvsNodes


def sfmPipeline(graph):
    """
    Instantiate a SfM pipeline inside 'graph'.
    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated

    Returns:
        list of Node: the created nodes
    """
    cameraInit = graph.addNewNode('CameraInit')

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
    return [
        cameraInit,
        featureExtraction,
        imageMatching,
        featureMatching,
        structureFromMotion
    ]


def mvsPipeline(graph, sfm=None):
    """
    Instantiate a MVS pipeline inside 'graph'.

    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated
        sfm (Node, optional): if specified, connect the MVS pipeline to this StructureFromMotion node

    Returns:
        list of Node: the created nodes
    """
    if sfm and not sfm.nodeType == "StructureFromMotion":
        raise ValueError("Invalid node type. Expected StructureFromMotion, got {}.".format(sfm.nodeType))

    prepareDenseScene = graph.addNewNode('PrepareDenseScene',
                                         input=sfm.output if sfm else "")
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

    return [
        prepareDenseScene,
        cameraConnection,
        depthMap,
        depthMapFilter,
        meshing,
        texturing
    ]
