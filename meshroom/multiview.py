# Multiview pipeline version
__version__ = "2.2"

import os

from meshroom.core.graph import Graph, GraphModification

# Supported image extensions
imageExtensions = ('.jpg', '.jpeg', '.tif', '.tiff', '.png', '.exr', '.rw2', '.cr2', '.nef', '.arw')


def isImageFile(filepath):
    """ Return whether filepath is a path to an image file supported by Meshroom. """
    return os.path.splitext(filepath)[1].lower() in imageExtensions


def findImageFiles(folder):
    """
    Return all files that are images in 'folder' based on their extensions.

    Args:
        folder (str): the folder to look into

    Returns:
        list: the list of image files.
    """
    return [os.path.join(folder, filename) for filename in os.listdir(folder) if isImageFile(filename)]


def photogrammetry(inputImages=list(), inputViewpoints=list(), inputIntrinsics=list(), output=''):
    """
    Create a new Graph with a complete photogrammetry pipeline.

    Args:
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
        cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        cameraInit.viewpoints.extend(inputViewpoints)
        cameraInit.intrinsics.extend(inputIntrinsics)

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

    # store current pipeline version in graph header
    graph.header.update({'pipelineVersion': __version__})

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
                                     featuresFolders=[featureExtraction.output])
    featureMatching = graph.addNewNode('FeatureMatching',
                                       input=imageMatching.input,
                                       featuresFolders=imageMatching.featuresFolders,
                                       imagePairsList=imageMatching.output)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=featureMatching.input,
                                           featuresFolders=featureMatching.featuresFolders,
                                           matchesFolders=[featureMatching.output])
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
    depthMap = graph.addNewNode('DepthMap',
                                input=prepareDenseScene.input,
                                imagesFolder=prepareDenseScene.output)
    depthMapFilter = graph.addNewNode('DepthMapFilter',
                                      input=depthMap.input,
                                      depthMapsFolder=depthMap.output)
    meshing = graph.addNewNode('Meshing',
                               input=depthMapFilter.input,
                               depthMapsFolder=depthMapFilter.depthMapsFolder,
                               depthMapsFilterFolder=depthMapFilter.output)
    meshFiltering = graph.addNewNode('MeshFiltering',
                                     inputMesh=meshing.outputMesh)
    texturing = graph.addNewNode('Texturing',
                                 input=meshing.output,
                                 imagesFolder=depthMap.imagesFolder,
                                 inputMesh=meshFiltering.outputMesh)

    return [
        prepareDenseScene,
        depthMap,
        depthMapFilter,
        meshing,
        meshFiltering,
        texturing
    ]


def sfmAugmentation(graph, sourceSfm, withMVS=False):
    """
    Create a SfM augmentation inside 'graph'.

    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated
        sourceSfm (Node, optional): if specified, connect the MVS pipeline to this StructureFromMotion node
        withMVS (bool): whether to create a MVS pipeline after the augmented SfM branch

    Returns:
        tuple: the created nodes (sfmNodes, mvsNodes)
    """
    cameraInit = graph.addNewNode('CameraInit')

    featureExtraction = graph.addNewNode('FeatureExtraction',
                                         input=cameraInit.output)
    imageMatchingMulti = graph.addNewNode('ImageMatchingMultiSfM',
                                          input=featureExtraction.input,
                                          featuresFolders=[featureExtraction.output]
                                          )
    featureMatching = graph.addNewNode('FeatureMatching',
                                       input=imageMatchingMulti.outputCombinedSfM,
                                       featuresFolders=imageMatchingMulti.featuresFolders,
                                       imagePairsList=imageMatchingMulti.output)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=featureMatching.input,
                                           featuresFolders=featureMatching.featuresFolders,
                                           matchesFolders=[featureMatching.output])
    graph.addEdge(sourceSfm.output, imageMatchingMulti.inputB)

    sfmNodes = [
        cameraInit,
        featureMatching,
        imageMatchingMulti,
        featureMatching,
        structureFromMotion
    ]

    mvsNodes = []

    if withMVS:
        mvsNodes = mvsPipeline(graph, structureFromMotion)

    return sfmNodes, mvsNodes
