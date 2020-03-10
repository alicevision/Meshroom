__version__ = "2.0"

import os
import json
import psutil
import shutil
import tempfile

from meshroom.core import desc


Viewpoint = [
    desc.IntParam(name="viewId", label="Id", description="Image UID", value=-1, uid=[0], range=None),
    desc.IntParam(name="poseId", label="Pose Id", description="Pose Id", value=-1, uid=[0], range=None),
    desc.File(name="path", label="Image Path", description="Image Filepath", value="", uid=[0]),
    desc.IntParam(name="intrinsicId", label="Intrinsic", description="Internal Camera Parameters", value=-1, uid=[0], range=None),
    desc.IntParam(name="rigId", label="Rig", description="Rig Parameters", value=-1, uid=[0], range=None),
    desc.IntParam(name="subPoseId", label="Rig Sub-Pose", description="Rig Sub-Pose Parameters", value=-1, uid=[0], range=None),
    desc.StringParam(name="metadata", label="Image Metadata", description="", value="", uid=[], advanced=True),
]

Intrinsic = [
    desc.IntParam(name="intrinsicId", label="Id", description="Intrinsic UID", value=-1, uid=[0], range=None),
    desc.FloatParam(name="pxInitialFocalLength", label="Initial Focal Length", description="Initial Guess on the Focal Length", value=-1.0, uid=[0], range=None),
    desc.FloatParam(name="pxFocalLength", label="Focal Length", description="Known/Calibrated Focal Length", value=-1.0, uid=[0], range=None),
    desc.ChoiceParam(name="type", label="Camera Type", description="Camera Type", value="", values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4'], exclusive=True, uid=[0]),
    desc.IntParam(name="width", label="Width", description="Image Width", value=0, uid=[], range=(0, 10000, 1)),
    desc.IntParam(name="height", label="Height", description="Image Height", value=0, uid=[], range=(0, 10000, 1)),
    desc.StringParam(name="serialNumber", label="Serial Number", description="Device Serial Number (camera and lens combined)", value="", uid=[]),
    desc.GroupAttribute(name="principalPoint", label="Principal Point", description="", groupDesc=[
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
            uid=[0],
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
            uid=[0],
            advanced=True
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
            label='Output SfMData File',
            description='''Output SfMData.''',
            value=desc.Node.internalFolder + 'cameraInit.sfm',
            uid=[],
        ),
    ]

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
            # logging.debug(' - commandLine:', cmd)
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

        except Exception:
            raise
        finally:
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
            views = node.viewpoints.getPrimitiveValue(exportDefault=False)

            # convert the metadata string into a map
            for view in views:
                if 'metadata' in view:
                    view['metadata'] = json.loads(view['metadata'])

            sfmData = {
                "version": [1, 0, 0],
                "views": views + newViews,
                "intrinsics": intrinsics,
                "featureFolder": "",
                "matchingFolder": "",
            }
            node.viewpointsFile = (node.nodeDesc.internalFolder + '/viewpoints.sfm').format(**node._cmdVars)
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
