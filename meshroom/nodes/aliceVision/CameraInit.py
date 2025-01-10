__version__ = "12.0"

import os
import json
import psutil
import shutil
import tempfile
import logging

from meshroom.core import desc, Version
from meshroom.core.utils import RAW_COLOR_INTERPRETATION, VERBOSE_LEVEL
from meshroom.multiview import FilesByType, findFilesByTypeInFolder

Viewpoint = [
    desc.IntParam(
        name="viewId",
        label="ID",
        description="Image UID.",
        value=-1,
        range=None,
    ),
    desc.IntParam(
        name="poseId",
        label="Pose ID",
        description="Pose ID.",
        value=-1,
        range=None,
    ),
    desc.File(
        name="path",
        label="Image Path",
        description="Image filepath.",
        value="",
    ),
    desc.IntParam(
        name="intrinsicId",
        label="Intrinsic",
        description="Internal camera parameters.",
        value=-1,
        range=None,
    ),
    desc.IntParam(
        name="rigId",
        label="Rig",
        description="Rig parameters.",
        value=-1,
        range=None,
    ),
    desc.IntParam(
        name="subPoseId",
        label="Rig Sub-Pose",
        description="Rig sub-pose parameters.",
        value=-1,
        range=None,
    ),
    desc.StringParam(
        name="metadata",
        label="Image Metadata",
        description="The configuration of the Viewpoints is based on the images' metadata.\n"
                    "The important ones are:\n"
                    " - Focal Length: the focal length in mm.\n"
                    " - Make and Model: this information allows to convert the focal in mm into a focal length in "
                    "pixels using an embedded sensor database.\n"
                    " - Serial Number: allows to uniquely identify a device so multiple devices with the same Make, "
                    "Model can be differentiated and their internal parameters are optimized separately.",
        value="",
        invalidate=False,
        advanced=True,
    ),
]

Intrinsic = [
    desc.IntParam(
        name="intrinsicId",
        label="ID",
        description="Intrinsic UID.",
        value=-1,
        range=None,
    ),
    desc.FloatParam(
        name="initialFocalLength",
        label="Initial Focal Length",
        description="Initial guess on the focal length (in mm).\n"
                    "When we have an initial value from EXIF, this value is not accurate but it cannot be wrong.\n"
                    "So this value is used to limit the range of possible values in the optimization.\n"
                    "If this value is set to -1, it will not be used and the focal length will not be bounded.",
        value=-1.0,
        range=None,
    ),
    desc.FloatParam(
        name="focalLength",
        label="Focal Length",
        description="Known/calibrated focal length (in mm).",
        value=1000.0,
        range=(0.0, 10000.0, 1.0),
    ),
    desc.FloatParam(
        name="pixelRatio",
        label="Pixel Ratio",
        description="Ratio between the pixel width and the pixel height.",
        value=1.0,
        range=(0.0, 10.0, 0.1),
    ),
    desc.BoolParam(
        name="pixelRatioLocked",
        label="Pixel Ratio Locked",
        description="The pixel ratio value is locked for estimation.",
        value=True,
    ),
    desc.BoolParam(
        name="scaleLocked",
        label="Focal length Locked",
        description="The focal length is locked for estimation.",
        value=False,
    ),
    desc.BoolParam(
        name="offsetLocked",
        label="Optical Center Locked",
        description="The optical center coordinates are locked for estimation.",
        value=False,
    ),
    desc.BoolParam(
        name="distortionLocked",
        label="Distortion Locked",
        description="The distortion parameters are locked for estimation.",
        value=False,
    ),
    desc.ChoiceParam(
        name="type",
        label="Camera Type",
        description="Mathematical model used to represent a camera:\n"
                    " - pinhole: Simplest projective camera model without optical distortion "
                    "(focal and optical center).\n"
                    " - equidistant: Non-projective camera model suited for full-fisheye optics.\n"
                    " - equirectangular: Projection model used in panoramas.\n",
        value="pinhole",
        values=["pinhole", "equidistant", "equirectangular"],
    ),
    desc.ChoiceParam(
        name="distortionType",
        label="Distortion Type",
        description="Mathematical model used to represent the distortion:\n"
                    " - radialk1: radial distortion with one parameter.\n"
                    " - radialk3: radial distortion with three parameters (Best for pinhole cameras).\n"
                    " - radialk3pt: radial distortion with three parameters and normalized with the sum of parameters "
                    "(Best for equidistant cameras).\n"
                    " - brown: distortion with 3 radial and 2 tangential parameters.\n"
                    " - fisheye1: distortion with 1 parameter suited for fisheye optics (like 120deg FoV).\n"
                    " - fisheye4: distortion with 4 parameters suited for fisheye optics (like 120deg FoV).\n",
        value="radialk3",
        values=["none", "radialk1", "radialk3", "radialk3pt", "brown", "fisheye4", "fisheye1"],
    ),
    desc.IntParam(
        name="width",
        label="Width",
        description="Image width.",
        value=0,
        range=(0, 10000, 1),
    ),
    desc.IntParam(
        name="height",
        label="Height",
        description="Image height.",
        value=0,
        range=(0, 10000, 1),
    ),
    desc.FloatParam(
        name="sensorWidth",
        label="Sensor Width",
        description="Sensor width (in mm).",
        value=36.0,
        range=(0.0, 1000.0, 1.0),
    ),
    desc.FloatParam(
        name="sensorHeight",
        label="Sensor Height",
        description="Sensor height (in mm).",
        value=24.0,
        range=(0.0, 1000.0, 1.0),
    ),
    desc.StringParam(
        name="serialNumber",
        label="Serial Number",
        description="Device serial number (Camera UID and Lens UID combined).",
        value="",
    ),
    desc.GroupAttribute(
        name="principalPoint",
        label="Principal Point",
        description="Position of the optical center in the image (i.e. the sensor surface).",
        groupDesc=[
            desc.FloatParam(
                name="x",
                label="x",
                description="",
                value=0.0,
                range=(0.0, 10000.0, 1.0),
            ),
            desc.FloatParam(
                name="y",
                label="y",
                description="",
                value=0.0,
                range=(0.0, 10000.0, 1.0),
            ),
        ],
    ),
    desc.ChoiceParam(
        name="initializationMode",
        label="Initialization Mode",
        description="Defines how this intrinsic was initialized:\n"
                    " - calibrated: calibrated externally.\n"
                    " - estimated: estimated from metadata and/or sensor width.\n"
                    " - unknown: unknown camera parameters (can still have default value guess).\n"
                    " - none: not set.",
        values=["calibrated", "estimated", "unknown", "none"],
        value="none",
    ),
    desc.ChoiceParam(
        name="distortionInitializationMode",
        label="Distortion Initialization Mode",
        description="Defines how the distortion model and parameters were initialized:\n"
                    " - calibrated: calibrated externally.\n"
                    " - estimated: estimated from a database of generic calibration.\n"
                    " - unknown: unknown camera parameters (can still have default value guess).\n"
                    " - none: not set.",
        values=["calibrated", "estimated", "unknown", "none"],
        value="none",
    ),
    desc.ListAttribute(
        name="distortionParams",
        elementDesc=desc.FloatParam(
            name="p",
            label="",
            description="",
            value=0.0,
            range=(-0.1, 0.1, 0.01),
        ),
        label="Distortion Params",
        description="Distortion parameters.",
    ),
    desc.GroupAttribute(
        name="undistortionOffset",
        label="Undistortion Offset",
        description="Undistortion offset.",
        groupDesc=[
            desc.FloatParam(
                name="x",
                label="x",
                description="",
                value=0.0,
                range=(0.0, 10000.0, 1.0),
            ),
            desc.FloatParam(
                name="y",
                label="y",
                description="",
                value=0.0,
                range=(0.0, 10000.0, 1.0),
            ),
        ],
    ),
    desc.ListAttribute(
        name="undistortionParams",
        elementDesc=desc.FloatParam(
            name="p",
            label="",
            description="",
            value=0.0,
            range=(-0.1, 0.1, 0.01),
        ),
        label="Undistortion Params",
        description="Undistortion parameters."
    ),
    desc.BoolParam(
        name="locked",
        label="Locked",
        description="If the camera has been calibrated, the internal camera parameters (intrinsics) can be locked. "
                    "It should improve robustness and speed-up the reconstruction.",
        value=False,
    ),
]


def readSfMData(sfmFile):
    """ Read views and intrinsics from a .sfm file

    Args:
        sfmFile: the .sfm file containing views and intrinsics

    Returns:
        The views and intrinsics of the .sfm as two separate lists
    """
    # skip decoding errors to avoid potential exceptions due to non utf-8 characters in images metadata
    with open(sfmFile, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    intrinsicsKeys = [i.name for i in Intrinsic]

    intrinsics = [{k: v for k, v in item.items() if k in intrinsicsKeys} for item in data.get("intrinsics", [])]
    for intrinsic in intrinsics:
        pp = intrinsic.get('principalPoint', (0, 0))
        intrinsic['principalPoint'] = {}
        intrinsic['principalPoint']['x'] = pp[0]
        intrinsic['principalPoint']['y'] = pp[1]

        # convert empty string distortionParams (i.e: Pinhole model) to empty list
        distortionParams = intrinsic.get('distortionParams', '')
        if distortionParams == '':
            intrinsic['distortionParams'] = list()

        offset = intrinsic.get('undistortionOffset', (0, 0))
        intrinsic['undistortionOffset'] = {}
        intrinsic['undistortionOffset']['x'] = offset[0]
        intrinsic['undistortionOffset']['y'] = offset[1]

        undistortionParams = intrinsic.get('undistortionParams', '')
        if undistortionParams == '':
            intrinsic['undistortionParams'] = list()

    viewsKeys = [v.name for v in Viewpoint]
    views = [{k: v for k, v in item.items() if k in viewsKeys} for item in data.get("views", [])]
    for view in views:
        view['metadata'] = json.dumps(view['metadata'])  # convert metadata to string

    return views, intrinsics


class CameraInit(desc.AVCommandLineNode, desc.InitNode):
    commandLine = "aliceVision_cameraInit {allParams} --allowSingleView 1"  # don't throw an error if there is only one image

    size = desc.DynamicNodeSize("viewpoints")

    category = "Sparse Reconstruction"
    documentation = """
This node describes your dataset. It lists the Viewpoints candidates, the guess about the type of optic, the initial
focal length and which images are sharing the same internal camera parameters, as well as potential camera rigs.

When you import new images into Meshroom, this node is automatically configured from the analysis of the images' metadata.
The software can support images without any metadata but it is recommended to have them for robustness.

### Metadata
Metadata allow images to be grouped together and provide an initialization of the focal length (in pixel unit).
The needed metadata are:
 * **Focal Length**: the focal length in mm.
 * **Make** & **Model**: this information allows to convert the focal in mm into a focal length in pixels using an
 embedded sensor database.
 * **Serial Number**: allows to uniquely identify a device so multiple devices with the same Make, Model can be
 differentiated and their internal parameters are optimized separately (in the photogrammetry case).
"""

    inputs = [
        desc.ListAttribute(
            name="viewpoints",
            elementDesc=desc.GroupAttribute(
                name="viewpoint",
                label="Viewpoint",
                description="Viewpoint.",
                groupDesc=Viewpoint,
            ),
            label="Viewpoints",
            description="Input viewpoints.",
            group="",
        ),
        desc.ListAttribute(
            name="intrinsics",
            elementDesc=desc.GroupAttribute(
                name="intrinsic",
                label="Intrinsic",
                description="Intrinsic.",
                groupDesc=Intrinsic,
            ),
            label="Intrinsics",
            description="Camera intrinsics.",
            group="",
        ),
        desc.File(
            name="sensorDatabase",
            label="Sensor Database",
            description="Camera sensor with database path.",
            value="${ALICEVISION_SENSOR_DB}",
            invalidate=False,
        ),
        desc.File(
            name="lensCorrectionProfileInfo",
            label="LCP Info",
            description="Lens Correction Profile filepath or database directory.",
            value="${ALICEVISION_LENS_PROFILE_INFO}",
            invalidate=False,
        ),
        desc.BoolParam(
            name="lensCorrectionProfileSearchIgnoreCameraModel",
            label="LCP Generic Search",
            description="The lens name and camera maker are used to match the LCP database, but the camera model is ignored.",
            value=True,
            advanced=True,
        ),
        desc.FloatParam(
            name="defaultFieldOfView",
            label="Default Field Of View",
            description="Default value for the field of view (in degrees) used as an initialization value when there is "
                        "no focal or field of view in the image metadata.",
            value=45.0,
            range=(0.0, 180.0, 1.0),
            invalidate=False,
        ),
        desc.ChoiceParam(
            name="groupCameraFallback",
            label="Group Camera Fallback",
            description="If there is no serial number in the images' metadata, devices cannot be accurately identified.\n"
                        "Therefore, internal camera parameters cannot be shared among images reliably.\n"
                        "A fallback grouping strategy must be chosen:\n"
                        " - global: group images from comparable devices (same make/model/focal) globally.\n"
                        " - folder: group images from comparable devices only within the same folder.\n"
                        " - image: never group images from comparable devices.",
            values=["global", "folder", "image"],
            value="folder",
            invalidate=False,
        ),
        desc.ChoiceParam(
            name="rawColorInterpretation",
            label="RAW Color Interpretation",
            description="Allows to choose how RAW data are color processed:\n"
                        " - None: Debayering without any color processing.\n"
                        " - LibRawNoWhiteBalancing: Simple neutralization.\n"
                        " - LibRawWhiteBalancing: Use internal white balancing from libraw.\n"
                        " - DCPLinearProcessing: Use DCP color profile.\n"
                        " - DCPMetadata: Same as None with DCP info added in metadata.",
            values=RAW_COLOR_INTERPRETATION,
            value="DCPLinearProcessing" if os.environ.get("ALICEVISION_COLOR_PROFILE_DB", "") else "LibRawWhiteBalancing",
        ),
        desc.File(
            name="colorProfileDatabase",
            label="Color Profile Database",
            description="Color Profile database directory path.",
            value="${ALICEVISION_COLOR_PROFILE_DB}",
            enabled=lambda node: node.rawColorInterpretation.value.startswith("DCP"),
            invalidate=False,
        ),
        desc.BoolParam(
            name="errorOnMissingColorProfile",
            label="Error On Missing DCP Color Profile",
            description="When enabled, if no color profile is found for at least one image, then an error is thrown.\n"
                        "When disabled, if no color profile is found for some images, it will fallback to "
                        "libRawWhiteBalancing for those images.",
            value=True,
            enabled=lambda node: node.rawColorInterpretation.value.startswith("DCP"),
        ),
        desc.ChoiceParam(
            name="viewIdMethod",
            label="ViewId Method",
            description="Allows to choose the way the viewID is generated:\n"
                        " - metadata : Generate viewId from image metadata.\n"
                        " - filename : Generate viewId from filename using regex.",
            value="metadata",
            values=["metadata", "filename"],
            invalidate=False,
            advanced=True,
        ),
        desc.StringParam(
            name="viewIdRegex",
            label="ViewId Regex",
            description="Regex used to catch number used as viewId in filename."
                        "You should capture specific parts of the filename with parentheses to define matching elements."
                        " (only numbers will work)\n"
                        "Some examples of patterns:\n"
                        " - Match the longest number at the end of the filename (default value): "
                        r'".*?(\d+)"' + "\n" +
                        " - Match the first number found in filename: "
                        r'"(\d+).*"',
            value=r".*?(\d+)",
            invalidate=False,
            advanced=True,
            enabled=lambda node: node.viewIdMethod.value == "filename",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Output SfMData.",
            value=desc.Node.internalFolder + "cameraInit.sfm",
        ),
    ]

    def __init__(self):
        super(CameraInit, self).__init__()

    def initialize(self, node, inputs, recursiveInputs):
        # Reset graph inputs
        self.resetAttributes(node, ["viewpoints", "intrinsics"])

        filesByType = FilesByType()
        searchedForImages = False

        if recursiveInputs:
            filesByType.extend(findFilesByTypeInFolder(recursiveInputs, recursive=True))
            searchedForImages = True

        # Add views and intrinsics from a file if it was provided, or look for the images
        if len(inputs) == 1 and os.path.isfile(inputs[0]) and os.path.splitext(inputs[0])[-1] in ('.json', '.sfm'):
            views, intrinsics = readSfMData(inputs[0])
            self.extendAttributes(node, {"viewpoints": views, "intrinsics": intrinsics})
        else:
            filesByType.extend(findFilesByTypeInFolder(inputs, recursive=False))
            searchedForImages = True

        # If there was no input file, check that the directories do contain images
        if searchedForImages and not filesByType.images:
            raise ValueError("No valid input file or no image in the provided directories")

        views, intrinsics = self.buildIntrinsics(node, filesByType.images)
        self.setAttributes(node, {"viewpoints": views, "intrinsics": intrinsics})

    def upgradeTypes(self, intrinsic, itype):
        if itype == "pinhole":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "none"
            intrinsic['undistortionType'] = "none"

        elif itype == "radial1":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "radialk1"
            intrinsic['undistortionType'] = "none"

        elif itype == "radial3":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "radialk3"
            intrinsic['undistortionType'] = "none"

        elif itype == "brown":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "brown"
            intrinsic['undistortionType'] = "none"

        elif itype == "fisheye4":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "fisheye4"
            intrinsic['undistortionType'] = "none"

        elif itype == "fisheye1":
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "fisheye1"
            intrinsic['undistortionType'] = "none"

        elif itype == "equidistant":
            intrinsic['type'] = "equidistant"
            intrinsic['distortionType'] = "none"
            intrinsic['undistortionType'] = "none"

        elif itype == "equidistant_r3":
            intrinsic['type'] = "equidistant"
            intrinsic['distortionType'] = "radialk3pt"
            intrinsic['undistortionType'] = "none"

        else:
            intrinsic['type'] = "pinhole"
            intrinsic['distortionType'] = "none"
            intrinsic['undistortionType'] = "none"

    def upgradeAttributeValues(self, attrValues, fromVersion):

        # Starting with version 6, the principal point is now relative to the image center
        if fromVersion < Version(6, 0):
            for intrinsic in attrValues['intrinsics']:
                principalPoint = intrinsic['principalPoint']
                intrinsic['principalPoint'] = {
                    "x": int(principalPoint["x"] - 0.5 * intrinsic['width']),
                    "y": int(principalPoint["y"] - 0.5 * intrinsic['height'])
                    }

        # Starting with version 7, the focal length is now in mm
        if fromVersion < Version(7, 0):
            for intrinsic in attrValues['intrinsics']:
                pxInitialFocalLength = intrinsic['pxInitialFocalLength']
                pxFocalLength = intrinsic['pxFocalLength']
                sensorWidth = intrinsic['sensorWidth']
                width = intrinsic['width']
                focalLength = (pxFocalLength / width) * sensorWidth
                initialFocalLength = (pxInitialFocalLength / width) * sensorWidth
                intrinsic['initialFocalLength'] = initialFocalLength
                intrinsic['focalLength'] = focalLength
                intrinsic['pixelRatio'] = 1.0
                intrinsic['pixelRatioLocked'] = False

        # Upgrade types
        if fromVersion < Version(10, 0):
            for intrinsic in attrValues['intrinsics']:
                itype = intrinsic['type']
                self.upgradeTypes(intrinsic, itype)

        return attrValues

    def readSfMData(self, sfmFile):
        return readSfMData(sfmFile)

    def buildIntrinsics(self, node, additionalViews=()):
        """ Build intrinsics from node current views and optional additional views

        Args:
            node: the CameraInit node instance to build intrinsics for
            additionalViews: (optional) the new views (list of path to images) to add to the node's viewpoints

        Returns:
            The updated views and intrinsics as two separate lists
        """
        assert isinstance(node.nodeDesc, CameraInit)
        if node.graph:
            # make a copy of the node outside the graph
            # to change its cache folder without modifying the original node
            node = node.graph.copyNode(node)[0]

        tmpCache = tempfile.mkdtemp()
        node.updateInternals(tmpCache)

        try:
            os.makedirs(os.path.join(tmpCache, node.internalFolder))
            self.createViewpointsFile(node, additionalViews)
            cmd = self.buildCommandLine(node.chunks[0])
            logging.debug(' - commandLine: {}'.format(cmd))
            proc = psutil.Popen(cmd, stdout=None, stderr=None, shell=True)
            stdout, stderr = proc.communicate()
            # proc.wait()
            if proc.returncode != 0:
                raise RuntimeError('CameraInit failed with error code {}.\nCommand was: "{}".\n'.format(
                    proc.returncode, cmd)
                )

            # Reload result of aliceVision_cameraInit
            cameraInitSfM = node.output.value
            return readSfMData(cameraInitSfM)

        except Exception as e:
            logging.debug("[CameraInit] Error while building intrinsics: {}".format(str(e)))
            raise
        finally:
            if os.path.exists(tmpCache):
                logging.debug("[CameraInit] Remove temp files in: {}".format(tmpCache))
                shutil.rmtree(tmpCache)

    def createViewpointsFile(self, node, additionalViews=()):
        node.viewpointsFile = ""
        if node.viewpoints or additionalViews:
            newViews = []
            for path in additionalViews:  # format additional views to match json format
                newViews.append({"path": path})
            intrinsics = node.intrinsics.getPrimitiveValue(exportDefault=True)
            for intrinsic in intrinsics:
                intrinsic['principalPoint'] = [intrinsic['principalPoint']['x'], intrinsic['principalPoint']['y']]
                intrinsic['undistortionOffset'] = [intrinsic['undistortionOffset']['x'], intrinsic['undistortionOffset']['y']]
                intrinsic['undistortionType'] = 'none'
            views = node.viewpoints.getPrimitiveValue(exportDefault=False)

            # convert the metadata string into a map
            for view in views:
                if 'metadata' in view:
                    view['metadata'] = json.loads(view['metadata'])

            sfmData = {
                "version": [1, 2, 12],
                "views": views + newViews,
                "intrinsics": intrinsics,
                "featureFolder": "",
                "matchingFolder": "",
            }
            node.viewpointsFile = os.path.join(node.nodeDesc.internalFolder, 'viewpoints.sfm').format(**node._cmdVars)
            with open(node.viewpointsFile, 'w') as f:
                json.dump(sfmData, f, indent=4)

    def buildCommandLine(self, chunk):
        cmd = desc.CommandLineNode.buildCommandLine(self, chunk)
        if chunk.node.viewpointsFile:
            cmd += ' --input "{}"'.format(chunk.node.viewpointsFile)
        return cmd

    def processChunk(self, chunk):
        self.createViewpointsFile(chunk.node)
        desc.CommandLineNode.processChunk(self, chunk)
