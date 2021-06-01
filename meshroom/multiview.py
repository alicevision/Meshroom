# Multiview pipeline version
__version__ = "2.2"

import os

from meshroom.core.graph import Graph, GraphModification

# Supported image extensions
imageExtensions = (
    # bmp:
    '.bmp',
    # cineon:
    '.cin',
    # dds
    '.dds',
    # dpx:
    '.dpx',
    # gif:
    '.gif',
    # hdr:
    '.hdr', '.rgbe',
    # heif
    '.heic', '.heif', '.avif',
    # ico:
    '.ico',
    # iff:
    '.iff', '.z',
    # jpeg:
    '.jpg', '.jpe', '.jpeg', '.jif', '.jfif', '.jfi',
    # jpeg2000:
    '.jp2', '.j2k', '.j2c',
    # openexr:
    '.exr', '.sxr', '.mxr',
    # png:
    '.png',
    # pnm:
    '.ppm', '.pgm', '.pbm', '.pnm', '.pfm',
    # psd:
    '.psd', '.pdd', '.psb',
    # ptex:
    '.ptex', '.ptx',
    # raw:
    '.bay', '.bmq', '.cr2', '.cr3', '.crw', '.cs1', '.dc2', '.dcr', '.dng', '.erf', '.fff', '.k25', '.kdc', '.mdc', '.mos', '.mrw', '.nef', '.orf', '.pef', '.pxn', '.raf', '.raw', '.rdc', '.sr2', '.srf', '.x3f', '.arw', '.3fr', '.cine', '.ia', '.kc2', '.mef', '.nrw', '.qtk', '.rw2', '.sti', '.rwl', '.srw', '.drf', '.dsc', '.cap', '.iiq', '.rwz',
    # rla:
    '.rla',
    # sgi:
    '.sgi', '.rgb', '.rgba', '.bw', '.int', '.inta',
    # socket:
    '.socket',
    # softimage:
    '.pic',
    # tiff:
    '.tiff', '.tif', '.tx', '.env', '.sm', '.vsm',
    # targa:
    '.tga', '.tpic',
    # webp:
    'webp',
    # zfile:
    '.zfile',
    # osl:
    '.osl', '.oso', '.oslgroup', '.oslbody',
    )
videoExtensions = (
    '.avi', '.mov', '.qt',
    '.mkv', '.webm',
    '.mp4', '.mpg', '.mpeg', '.m2v', '.m4v',
    '.wmv',
    '.ogv', '.ogg',
    '.mxf',
    )
panoramaInfoExtensions = ('.xml')


def hasExtension(filepath, extensions):
    """ Return whether filepath is one of the following extensions. """
    return os.path.splitext(filepath)[1].lower() in extensions


class FilesByType:
    def __init__(self):
        self.images = []
        self.videos = []
        self.panoramaInfo = []
        self.other = []

    def __bool__(self):
        return self.images or self.videos or self.panoramaInfo

    def extend(self, other):
        self.images.extend(other.images)
        self.videos.extend(other.videos)
        self.panoramaInfo.extend(other.panoramaInfo)
        self.other.extend(other.other)

    def addFile(self, file):
        if hasExtension(file, imageExtensions):
            self.images.append(file)
        elif hasExtension(file, videoExtensions):
            self.videos.append(file)
        elif hasExtension(file, panoramaInfoExtensions):
            self.panoramaInfo.append(file)
        else:
            self.other.append(file)

    def addFiles(self, files):
        for file in files:
            self.addFile(file)


def findFilesByTypeInFolder(folder, recursive=False):
    """
    Return all files that are images in 'folder' based on their extensions.

    Args:
        folder (str): folder to look into or list of folder/files

    Returns:
        list: the list of image files with a supported extension.
    """
    inputFolders = []
    if isinstance(folder, (list, tuple)):
        inputFolders = folder
    else:
        inputFolders.append(folder)

    output = FilesByType()
    for currentFolder in inputFolders:
        if os.path.isfile(currentFolder):
            output.addFile(currentFolder)
            continue
        elif os.path.isdir(currentFolder):
            if recursive:
                for root, directories, files in os.walk(currentFolder):
                    for filename in files:
                        output.addFile(os.path.join(root, filename))
            else:
                output.addFiles([os.path.join(currentFolder, filename) for filename in os.listdir(currentFolder)])
        else:
            # if not a diretory or a file, it may be an expression
            import glob
            paths = glob.glob(currentFolder)
            filesByType = findFilesByTypeInFolder(paths, recursive=recursive)
            output.extend(filesByType)

    return output


def panoramaHdr(inputImages=None, inputViewpoints=None, inputIntrinsics=None, output='', graph=None):
    """
    Create a new Graph with a Panorama HDR pipeline.

    Args:
        inputImages (list of str, optional): list of image file paths
        inputViewpoints (list of Viewpoint, optional): list of Viewpoints
        output (str, optional): the path to export reconstructed model to

    Returns:
        Graph: the created graph
    """
    if not graph:
        graph = Graph('PanoramaHDR')
    with GraphModification(graph):
        nodes = panoramaHdrPipeline(graph)
        cameraInit = nodes[0]
        if inputImages:
            cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        if inputViewpoints:
            cameraInit.viewpoints.extend(inputViewpoints)
        if inputIntrinsics:
            cameraInit.intrinsics.extend(inputIntrinsics)

        if output:
            imageProcessing = nodes[-1]
            graph.addNewNode('Publish', output=output, inputFiles=[imageProcessing.outputImages])

    return graph

def panoramaFisheyeHdr(inputImages=None, inputViewpoints=None, inputIntrinsics=None, output='', graph=None):
    if not graph:
        graph = Graph('PanoramaFisheyeHDR')
    with GraphModification(graph):
        panoramaHdr(inputImages, inputViewpoints, inputIntrinsics, output, graph)
        for panoramaInit in graph.nodesOfType("PanoramaInit"):
            panoramaInit.attribute("useFisheye").value = True
        for featureExtraction in graph.nodesOfType("FeatureExtraction"):
            # when using fisheye images, 'sift' performs better than 'dspsift'
            featureExtraction.attribute("describerTypes").value = ['sift']
            # when using fisheye images, the overlap between images can be small
            # and thus requires many features to get enough correspondances for cameras estimation
            featureExtraction.attribute("describerPreset").value = 'high'
    return graph

def panoramaHdrPipeline(graph):
    """
    Instantiate an PanoramaHDR pipeline inside 'graph'.
    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated

    Returns:
        list of Node: the created nodes
    """
    cameraInit = graph.addNewNode('CameraInit')
    try:
        # fisheye4 does not work well in the ParoramaEstimation, so here we avoid to use it.
        cameraInit.attribute('allowedCameraModels').value.remove("fisheye4")
    except ValueError:
        pass

    panoramaPrepareImages = graph.addNewNode('PanoramaPrepareImages',
                               input=cameraInit.output)

    ldr2hdrSampling = graph.addNewNode('LdrToHdrSampling',
                               input=panoramaPrepareImages.output)

    ldr2hdrCalibration = graph.addNewNode('LdrToHdrCalibration',
                               input=ldr2hdrSampling.input,
                               userNbBrackets=ldr2hdrSampling.userNbBrackets,
                               byPass=ldr2hdrSampling.byPass,
                               channelQuantizationPower=ldr2hdrSampling.channelQuantizationPower,
                               samples=ldr2hdrSampling.output)

    ldr2hdrMerge = graph.addNewNode('LdrToHdrMerge',
                               input=ldr2hdrCalibration.input,
                               userNbBrackets=ldr2hdrCalibration.userNbBrackets,
                               byPass=ldr2hdrCalibration.byPass,
                               channelQuantizationPower=ldr2hdrCalibration.channelQuantizationPower,
                               response=ldr2hdrCalibration.response)

    featureExtraction = graph.addNewNode('FeatureExtraction',
                                         input=ldr2hdrMerge.outSfMData,
                                         describerQuality='high')

    panoramaInit = graph.addNewNode('PanoramaInit',
                                     input=featureExtraction.input,
                                     dependency=[featureExtraction.output]  # Workaround for tractor submission with a fake dependency
                                     )

    imageMatching = graph.addNewNode('ImageMatching',
                                     input=panoramaInit.outSfMData,
                                     featuresFolders=[featureExtraction.output],
                                     method='FrustumOrVocabularyTree')

    featureMatching = graph.addNewNode('FeatureMatching',
                                       input=imageMatching.input,
                                       featuresFolders=imageMatching.featuresFolders,
                                       imagePairsList=imageMatching.output,
                                       describerTypes=featureExtraction.describerTypes)

    panoramaEstimation = graph.addNewNode('PanoramaEstimation',
                                          input=featureMatching.input,
                                          featuresFolders=featureMatching.featuresFolders,
                                          matchesFolders=[featureMatching.output],
                                          describerTypes=featureMatching.describerTypes)

    panoramaOrientation = graph.addNewNode('SfMTransform',
                                           input=panoramaEstimation.output,
                                           method='from_single_camera')

    panoramaWarping = graph.addNewNode('PanoramaWarping',
                                       input=panoramaOrientation.output)

    panoramaSeams =  graph.addNewNode('PanoramaSeams',
                                       input=panoramaWarping.input,
                                       warpingFolder=panoramaWarping.output
                                       )

    panoramaCompositing = graph.addNewNode('PanoramaCompositing',
                                           input=panoramaSeams.input,
                                           warpingFolder=panoramaSeams.warpingFolder,
                                           labels=panoramaSeams.output
                                        )

    panoramaMerging = graph.addNewNode('PanoramaMerging',
                                           input=panoramaCompositing.input,
                                           compositingFolder=panoramaCompositing.output
                                        )

    imageProcessing = graph.addNewNode('ImageProcessing',
                                       input=panoramaMerging.outputPanorama,
                                       fixNonFinite=True,
                                       fillHoles=True,
                                       extension='exr')

    return [
        cameraInit,
        featureExtraction,
        panoramaInit,
        imageMatching,
        featureMatching,
        panoramaEstimation,
        panoramaOrientation,
        panoramaWarping,
        panoramaSeams,
        panoramaCompositing,
        panoramaMerging,
        imageProcessing,
    ]



def photogrammetry(inputImages=list(), inputViewpoints=list(), inputIntrinsics=list(), output='', graph=None):
    """
    Create a new Graph with a complete photogrammetry pipeline.

    Args:
        inputImages (list of str, optional): list of image file paths
        inputViewpoints (list of Viewpoint, optional): list of Viewpoints
        output (str, optional): the path to export reconstructed model to

    Returns:
        Graph: the created graph
    """
    if not graph:
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
                                       imagePairsList=imageMatching.output,
                                       describerTypes=featureExtraction.describerTypes)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=featureMatching.input,
                                           featuresFolders=featureMatching.featuresFolders,
                                           matchesFolders=[featureMatching.output],
                                           describerTypes=featureMatching.describerTypes)
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
                               depthMapsFolder=depthMapFilter.output)
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
                                       imagePairsList=imageMatchingMulti.output,
                                       describerTypes=featureExtraction.describerTypes)
    structureFromMotion = graph.addNewNode('StructureFromMotion',
                                           input=featureMatching.input,
                                           featuresFolders=featureMatching.featuresFolders,
                                           matchesFolders=[featureMatching.output],
                                           describerTypes=featureMatching.describerTypes)
    graph.addEdge(sourceSfm.output, imageMatchingMulti.inputB)

    sfmNodes = [
        cameraInit,
        featureExtraction,
        imageMatchingMulti,
        featureMatching,
        structureFromMotion
    ]

    mvsNodes = []

    if withMVS:
        mvsNodes = mvsPipeline(graph, structureFromMotion)

    return sfmNodes, mvsNodes


def cameraTrackingPipeline(graph, sourceSfm=None):
    """
    Instantiate a camera tracking pipeline inside 'graph'.

    Args:
        graph (Graph/UIGraph): the graph in which nodes should be instantiated

    Returns:
        list of Node: the created nodes
    """

    with GraphModification(graph):
        if sourceSfm is None:
            cameraInitT, featureExtractionT, imageMatchingT, featureMatchingT, structureFromMotionT = sfmPipeline(graph)
        else:
            sfmNodes, _ = sfmAugmentation(graph, sourceSfm)
            cameraInitT, featureExtractionT, imageMatchingT, featureMatchingT, structureFromMotionT = sfmNodes

        distortionCalibrationT = graph.addNewNode('DistortionCalibration',
                                                  input=cameraInitT.output)

        graph.removeEdge(featureMatchingT.input)
        graph.addEdge(distortionCalibrationT.outSfMData, featureMatchingT.input)

        imageMatchingT.attribute("nbMatches").value = 5  # voctree nb matches
        imageMatchingT.attribute("nbNeighbors").value = 10

        structureFromMotionT.attribute("minNumberOfMatches").value = 0
        structureFromMotionT.attribute("minInputTrackLength").value = 5
        structureFromMotionT.attribute("minNumberOfObservationsForTriangulation").value = 3
        structureFromMotionT.attribute("minAngleForTriangulation").value = 1.0
        structureFromMotionT.attribute("minAngleForLandmark").value = 0.5

        exportAnimatedCameraT = graph.addNewNode('ExportAnimatedCamera', input=structureFromMotionT.output)
        if sourceSfm:
            graph.addEdge(sourceSfm.output, exportAnimatedCameraT.sfmDataFilter)

    # store current pipeline version in graph header
    graph.header.update({'pipelineVersion': __version__})

    return [
        cameraInitT,
        featureExtractionT,
        imageMatchingT,
        featureMatchingT,
        distortionCalibrationT,
        structureFromMotionT,
        exportAnimatedCameraT,
        ]


def cameraTracking(inputImages=list(), inputViewpoints=list(), inputIntrinsics=list(), output='', graph=None):
    if not graph:
        graph = Graph('Camera Tracking')
    with GraphModification(graph):
        trackingNodes = cameraTrackingPipeline(graph)
        cameraInit = trackingNodes[0]
        cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        cameraInit.viewpoints.extend(inputViewpoints)
        cameraInit.intrinsics.extend(inputIntrinsics)

        if output:
            exportNode = trackingNodes[-1]
            graph.addNewNode('Publish', output=output, inputFiles=[exportNode.output])

    return graph


def photogrammetryAndCameraTracking(inputImages=list(), inputViewpoints=list(), inputIntrinsics=list(), output='', graph=None):
    if not graph:
        graph = Graph('Photogrammetry And Camera Tracking')
    with GraphModification(graph):
        cameraInit, featureExtraction, imageMatching, featureMatching, structureFromMotion = sfmPipeline(graph)

        cameraInitT, featureExtractionT, imageMatchingMultiT, featureMatchingT, distortionCalibrationT, structureFromMotionT, exportAnimatedCameraT = cameraTrackingPipeline(graph, structureFromMotion)

        cameraInit.viewpoints.extend([{'path': image} for image in inputImages])
        cameraInit.viewpoints.extend(inputViewpoints)
        cameraInit.intrinsics.extend(inputIntrinsics)

        if output:
            graph.addNewNode('Publish', output=output, inputFiles=[exportAnimatedCameraT.output])

    return graph

