__version__ = "6.0"

import os
import json
import psutil
import shutil
import tempfile
import logging

from meshroom.core import desc, Version


Viewpoint = [
    desc.IntParam(name="viewId", label="Id", description="Image UID", value=-1, uid=[0], range=None),
    desc.IntParam(name="poseId", label="Pose Id", description="Pose Id", value=-1, uid=[0], range=None),
    desc.File(name="path", label="Image Path", description="Image Filepath", value="", uid=[0]),
    desc.IntParam(name="intrinsicId", label="Intrinsic", description="Internal Camera Parameters", value=-1, uid=[0], range=None),
    desc.IntParam(name="rigId", label="Rig", description="Rig Parameters", value=-1, uid=[0], range=None),
    desc.IntParam(name="subPoseId", label="Rig Sub-Pose", description="Rig Sub-Pose Parameters", value=-1, uid=[0], range=None),
    desc.StringParam(name="metadata", label="Image Metadata",
                     description="The configuration of the Viewpoints is based on the images metadata.\n"
                                 "The important ones are:\n"
                     " * Focal Length: the focal length in mm.\n"
                     " * Make and Model: this information allows to convert the focal in mm into a focal length in pixel using an embedded sensor database.\n"
                     " * Serial Number: allows to uniquely identify a device so multiple devices with the same Make, Model can be differentiated and their internal parameters are optimized separately.",
                     value="", uid=[], advanced=True),
]

Intrinsic = [
    desc.IntParam(name="intrinsicId", label="Id", description="Intrinsic UID", value=-1, uid=[0], range=None),
    desc.FloatParam(name="pxInitialFocalLength", label="Initial Focal Length",
                    description="Initial Guess on the Focal Length (in pixels). \n"
                    "When we have an initial value from EXIF, this value is not accurate but cannot be wrong. \n"
                    "So this value is used to limit the range of possible values in the optimization. \n"
                    "If you put -1, this value will not be used and the focal length will not be bounded.",
                    value=-1.0, uid=[0], range=None),
    desc.GroupAttribute(name="pxFocalLength", label="Focal Length", description="Known/Calibrated Focal Length (in pixels)", groupDesc=[
        desc.FloatParam(name="x", label="x", description="", value=-1, uid=[], range=(0, 10000, 1)),
        desc.FloatParam(name="y", label="y", description="", value=-1, uid=[], range=(0, 10000, 1)),
        ]),
    desc.ChoiceParam(name="type", label="Camera Type",
                     description="Mathematical Model used to represent a camera:\n"
                     " * pinhole: Simplest projective camera model without optical distortion (focal and optical center).\n"
                     " * radial1: Pinhole camera with one radial distortion parameter\n"
                     " * radial3: Pinhole camera with 3 radial distortion parameters\n"
                     " * brown: Pinhole camera with 3 radial and 2 tangential distortion parameters\n"
                     " * fisheye4: Pinhole camera with 4 distortion parameters suited for fisheye optics (like 120deg FoV)\n"
                     " * equidistant_r3: Non-projective camera model suited for full-fisheye optics (like 180deg FoV)\n"
                     " * 3deanamorphic4: Pinhole camera with a 4 anamorphic distortion coefficients.\n"
                     " * 3declassicld: Pinhole camera with a 10 anamorphic distortion coefficients\n"
                     " * 3deradial4: Pinhole camera with 3DE radial4 model\n",
                     value="", values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4', 'equidistant_r3', '3deanamorphic4', '3declassicld', '3deradial4'], exclusive=True, uid=[0]),
    desc.IntParam(name="width", label="Width", description="Image Width", value=0, uid=[], range=(0, 10000, 1)),
    desc.IntParam(name="height", label="Height", description="Image Height", value=0, uid=[], range=(0, 10000, 1)),
    desc.FloatParam(name="sensorWidth", label="Sensor Width", description="Sensor Width (mm)", value=36, uid=[], range=(0, 1000, 1)),
    desc.FloatParam(name="sensorHeight", label="Sensor Height", description="Sensor Height (mm)", value=24, uid=[], range=(0, 1000, 1)),
    desc.StringParam(name="serialNumber", label="Serial Number", description="Device Serial Number (Camera UID and Lens UID combined)", value="", uid=[]),
    desc.GroupAttribute(name="principalPoint", label="Principal Point", description="Position of the Optical Center in the Image (i.e. the sensor surface).", groupDesc=[
        desc.FloatParam(name="x", label="x", description="", value=0, uid=[], range=(0, 10000, 1)),
        desc.FloatParam(name="y", label="y", description="", value=0, uid=[], range=(0, 10000, 1)),
        ]),

    desc.ChoiceParam(name="initializationMode", label="Initialization Mode",
                     description="Defines how this Intrinsic was initialized:\n"
                                 " * calibrated: calibrated externally.\n"
                                 " * estimated: estimated from metadata and/or sensor width. \n"
                                 " * unknown: unknown camera parameters (can still have default value guess)\n"
                                 " * none: not set",
                     values=("calibrated", "estimated", "unknown", "none"),
                     value="none",
                     exclusive=True,
                     uid=[],
                     advanced=True
                     ),

    desc.ListAttribute(
            name="distortionParams",
            elementDesc=desc.FloatParam(name="p", label="", description="", value=0.0, uid=[0], range=(-0.1, 0.1, 0.01)),
            label="Distortion Params",
            description="Distortion Parameters",
        ),
    desc.BoolParam(name='locked', label='Locked',
                   description='If the camera has been calibrated, the internal camera parameters (intrinsics) can be locked. It should improve robustness and speedup the reconstruction.',
                   value=False, uid=[0]),
]

def readSfMData(sfmFile):
    """ Read views and intrinsics from a .sfm file

    Args:
        sfmFile: the .sfm file containing views and intrinsics

    Returns:
        The views and intrinsics of the .sfm as two separate lists
    """
    import io  # use io.open for Python2/3 compatibility (allow to specify encoding + errors handling)
    # skip decoding errors to avoid potential exceptions due to non utf-8 characters in images metadata
    with io.open(sfmFile, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    intrinsicsKeys = [i.name for i in Intrinsic]

    intrinsics = [{k: v for k, v in item.items() if k in intrinsicsKeys} for item in data.get("intrinsics", [])]
    for intrinsic in intrinsics:
        pp = intrinsic['principalPoint']
        intrinsic['principalPoint'] = {}
        intrinsic['principalPoint']['x'] = pp[0]
        intrinsic['principalPoint']['y'] = pp[1]

        f = intrinsic['pxFocalLength']
        intrinsic['pxFocalLength'] = {}
        intrinsic['pxFocalLength']['x'] = f[0]
        intrinsic['pxFocalLength']['y'] = f[1]

        # convert empty string distortionParams (i.e: Pinhole model) to empty list
        if intrinsic['distortionParams'] == '':
            intrinsic['distortionParams'] = list()

    viewsKeys = [v.name for v in Viewpoint]
    views = [{k: v for k, v in item.items() if k in viewsKeys} for item in data.get("views", [])]
    for view in views:
        view['metadata'] = json.dumps(view['metadata'])  # convert metadata to string

    return views, intrinsics

class CameraInit(desc.CommandLineNode):
    commandLine = 'aliceVision_cameraInit {allParams} --allowSingleView 1' # don't throw an error if there is only one image

    size = desc.DynamicNodeSize('viewpoints')

    category = 'Sparse Reconstruction'
    documentation = '''
This node describes your dataset. It lists the Viewpoints candidates, the guess about the type of optic, the initial focal length
and which images are sharing the same internal camera parameters, as well as potential cameras rigs.

When you import new images into Meshroom, this node is automatically configured from the analysis of the image metadata.
The software can support images without any metadata but it is recommended to have them for robustness.

### Metadata
Metadata allows images to be grouped together and provides an initialization of the focal length (in pixel unit).
The metadata needed are:
 * **Focal Length**: the focal length in mm.
 * **Make** & **Model**: this information allows to convert the focal in mm into a focal length in pixel using an embedded sensor database.
 * **Serial Number**: allows to uniquely identify a device so multiple devices with the same Make, Model can be differentiated and their internal parameters are optimized separately (in the photogrammetry case).
'''

    inputs = [
        desc.ListAttribute(
            name="viewpoints",
            elementDesc=desc.GroupAttribute(name="viewpoint", label="Viewpoint", description="", groupDesc=Viewpoint),
            label="Viewpoints",
            description="Input viewpoints",
            group="",
        ),
        desc.ListAttribute(
            name="intrinsics",
            elementDesc=desc.GroupAttribute(name="intrinsic", label="Intrinsic", description="", groupDesc=Intrinsic),
            label="Intrinsics",
            description="Camera Intrinsics",
            group="",
        ),
        desc.File(
            name='sensorDatabase',
            label='Sensor Database',
            description='''Camera sensor width database path.''',
            value=os.environ.get('ALICEVISION_SENSOR_DB', ''),
            uid=[],
        ),
        desc.FloatParam(
            name='defaultFieldOfView',
            label='Default Field Of View',
            description='Empirical value for the field of view in degree.',
            value=45.0,
            range=(0, 180.0, 1),
            uid=[],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='groupCameraFallback',
            label='Group Camera Fallback',
            description="If there is no serial number in image metadata, devices cannot be accurately identified.\n"
                        "Therefore, internal camera parameters cannot be shared among images reliably.\n"
                        "A fallback grouping strategy must be chosen:\n"
                        " * global: group images from comparable devices (same make/model/focal) globally.\n"
                        " * folder: group images from comparable devices only within the same folder.\n"
                        " * image: never group images from comparable devices",
            values=['global', 'folder', 'image'],
            value='folder',
            exclusive=True,
            uid=[],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='allowedCameraModels',
            label='Allowed Camera Models',
            description='the Camera Models that can be attributed.',
            value=['pinhole', 'radial1', 'radial3', 'brown', 'fisheye4', 'fisheye1', '3deanamorphic4', '3deradial4', '3declassicld'],
            values=['pinhole', 'radial1', 'radial3', 'brown', 'fisheye4', 'fisheye1', '3deanamorphic4', '3deradial4', '3declassicld'],
            exclusive=False,
            uid=[],
            joinChar=',',
            advanced=True,
        ),
        desc.BoolParam(
            name='useInternalWhiteBalance',
            label='Apply internal white balance',
            description='Apply image white balance (Only for raw images)',
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='viewIdMethod',
            label='ViewId Method',
            description="Allows to choose the way the viewID is generated:\n"
                        " * metadata : Generate viewId from image metadata.\n"
                        " * filename : Generate viewId from file names using regex.",
            value='metadata',
            values=['metadata', 'filename'],
            exclusive=True,
            uid=[],
            advanced=True,
        ),
        desc.StringParam(
            name='viewIdRegex',
            label='ViewId Regex',
            description='Regex used to catch number used as viewId in filename.'
                        'You should capture specific parts of the filename with parenthesis to define matching elements. (only number will works)\n'
                        'Some examples of patterns:\n'
                        ' - Match the longest number at the end of filename (default value): ".*?(\d+)"\n'
                        ' - Match the first number found in filename : "(\d+).*"\n',
            value='.*?(\d+)',
            uid=[],
            advanced=True,
            enabled=lambda node: node.viewIdMethod.value == 'filename',
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='SfMData',
            description='''Output SfMData.''',
            value=desc.Node.internalFolder + 'cameraInit.sfm',
            uid=[],
        ),
    ]

    def upgradeAttributeValues(self, attrValues, fromVersion):
        # Starting with version 5, the focal length is now split on x and y
        if fromVersion < Version(5, 0):
            for intrinsic in attrValues['intrinsics']:
                pxFocalLength = intrinsic['pxFocalLength']
                if not isinstance(pxFocalLength, dict):
                    intrinsic['pxFocalLength'] = {"x": pxFocalLength, "y": pxFocalLength}

        # Starting with version 6, the principal point is now relative to the image center
        if fromVersion < Version(6, 0):
            for intrinsic in attrValues['intrinsics']:
                principalPoint = intrinsic['principalPoint']
                intrinsic['principalPoint'] = {
                    "x": int(principalPoint["x"] - 0.5 * intrinsic['width']),
                    "y": int(principalPoint["y"] - 0.5 * intrinsic['height'])
                    }

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
                intrinsic['pxFocalLength'] = [intrinsic['pxFocalLength']['x'], intrinsic['pxFocalLength']['y']]
            views = node.viewpoints.getPrimitiveValue(exportDefault=False)

            # convert the metadata string into a map
            for view in views:
                if 'metadata' in view:
                    view['metadata'] = json.loads(view['metadata'])

            sfmData = {
                "version": [1, 2, 1],
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
