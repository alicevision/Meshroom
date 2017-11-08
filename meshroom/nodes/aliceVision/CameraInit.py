import os
import sys
from collections import OrderedDict
import json
import psutil
import shutil
import tempfile
import logging

from meshroom.core import desc
from meshroom.core.graph import GraphModification


Viewpoint = [
    desc.IntParam(name="id", label="Id", description="Image UID", value=-1, uid=[0], range=(0, 200, 1)),
    desc.File(name="image", label="Image", description="Image Filepath", value="", uid=[0, 1]),
    desc.IntParam(name="intrinsicId", label="Intrinsic", description="Internal Camera Parameters", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="rigId", label="Rig", description="Rig Parameters", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="rigSubPoseId", label="Rig Sub-Pose", description="Rig Sub-Pose Parameters", value=-1, uid=[0], range=(0, 200, 1)),
]

Intrinsic = [
    desc.IntParam(name="id", label="Id", description="Intrinsic UID", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="initialFocalLength", label="Initial Focal Length", description="Initial Guess on the Focal Length", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="focalLength", label="Focal Length", description="Known/Calibrated Focal Length", value=-1, uid=[0], range=(0, 200, 1)),
    desc.ChoiceParam(name="cameraType", label="Camera Type", description="Camera Type", value="", values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4'], exclusive=True, uid=[0]),
    desc.StringParam(name="deviceMake", label="Make", description="Camera Make", value="", uid=[]),
    desc.StringParam(name="deviceModel", label="Model", description="Camera Model", value="", uid=[]),
    desc.StringParam(name="sensorWidth", label="Sensor Width", description="Camera Sensor Width", value="", uid=[0]),
]


class CameraInit(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_cameraInit {allParams}'

    inputs = [
        desc.ListAttribute(
            name="viewpoints",
            elementDesc=desc.GroupAttribute(name="viewpoint", label="Viewpoint", description="", groupDesc=Viewpoint,
                                            group="allParams"),
            label="Viewpoints",
            description="Input viewpoints",
            group="",
        ),
        desc.ListAttribute(
            name="intrinsics",
            elementDesc=desc.GroupAttribute(name="intrinsic", label="Intrinsic", description="", groupDesc=Intrinsic,
                                            group="allParams"),
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
        desc.IntParam(
            name='defaultFocalLengthPix',
            label='Default Focal Length Pix',
            description='''Focal length in pixels.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='defaultSensorWidth',
            label='Default Sensor Width',
            description='''Sensor width in mm.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
        ),
        desc.StringParam(
            name='defaultIntrinsics',
            label='Default Intrinsics',
            description='''Intrinsics Kmatrix "f;0;ppx;0;f;ppy;0;0;1".''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='defaultCameraModel',
            label='Default Camera Model',
            description='''Camera model type (pinhole, radial1, radial3, brown, fisheye4).''',
            value='',
            values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4'],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='groupCameraModel',
            label='Group Camera Model',
            description='''* 0: each view have its own camera intrinsic parameters '''
                        '''* 1: view share camera intrinsic parameters based on metadata, '''
                        '''if no metadata each view has its own camera intrinsic parameters '''
                        '''* 2: view share camera intrinsic parameters based on metadata, '''
                        '''if no metadata they are grouped by folder''',
            value=1,
            values=[0, 1, 2],
            exclusive=True,
            uid=[0],
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
        desc.StringParam(
            name='_viewpointsUid',
            label='Internal Intrinsics Uid',
            description='',
            value='',
            uid=[],
            group='',
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Output SfMData.''',
            value='{cache}/{nodeType}/{uid0}',  # TODO
            uid=[],
        ),
        desc.File(
            name='outputSfm',
            label='Output SfM',
            description='''''',
            value='{cache}/{nodeType}/{uid0}/sfm_data.json',
            uid=[],
            group='',  # not a command line argument
        )
    ]

    def updateInternals(self, node):
        if not node.viewpoints:
            return
        lastViewpointsUid = node.attribute("_viewpointsUid").value
        if lastViewpointsUid == node.viewpoints.uid(1):
            return

        origCmdVars = node._cmdVars.copy()
        # Python3: with tempfile.TemporaryDirectory(prefix="Meshroom_CameraInit") as tmpCache
        tmpCache = tempfile.mkdtemp()
        localCmdVars = {
            'cache': tmpCache,
            'nodeType': node.nodeType,
        }
        node._buildCmdVars(localCmdVars)
        node._cmdVars = localCmdVars
        try:
            os.makedirs(os.path.join(tmpCache, node.internalFolder))
            self.createViewpointsFile(node)
            cmd = self.buildCommandLine(node.chunks[0])
            # logging.debug(' - commandLine:', cmd)
            subprocess = psutil.Popen(cmd, stdout=None, stderr=None, shell=True)
            stdout, stderr = subprocess.communicate()
            subprocess.wait()
            if subprocess.returncode != 0:
                logging.warning('CameraInit: Error on updateInternals of node "{}".'.format(node.name))
        except Exception:
            logging.warning('CameraInit: Error on updateInternals of node "{}".'.format(node.name))
            raise
        finally:
            node._cmdVars = origCmdVars
            shutil.rmtree(tmpCache)
        # TODO: reload result of aliceVision_cameraInit
        # cameraInitSfM = node.viewpointsFile  # localCmdVars['outputSfMValue']
        # jsonData = open(cameraInitSfM, 'r').read()
        # data = json.loads(jsonData)
        # with GraphModification(node.graph):
        #     node.viewpoints.value = data.get("views", [])
        #     node.intrinsics.value = data.get("intrinsics", [])

        node.attribute("_viewpointsUid").value = node.viewpoints.uid(1)

    def createViewpointsFile_new(self, node):
        if node.viewpoints:
            sfmData = {
                "version": [1, 0, 0],
                "views": node.viewpoints.getPrimitiveValue(exportDefault=False),
                "intrinsics": node.intrinsics.getPrimitiveValue(exportDefault=False),
            }
            node.viewpointsFile = '{cache}/{nodeType}/{uid0}/viewpoints.json'.format(**node._cmdVars)
            with open(node.viewpointsFile, 'w') as f:
                f.write(json.dumps(sfmData, indent=4))
                # python3: json.dumps(node.viewpoints, f, indent=4)

    def createViewpointsFile(self, node):
        """
        Temporary compatibility method.
        """
        if node.viewpoints:
            sfmData = {
                "resources": [v.get("image", "") for v in node.viewpoints.getPrimitiveValue(exportDefault=False)],
            }
            node.viewpointsFile = '{cache}/{nodeType}/{uid0}/viewpoints.json'.format(**node._cmdVars)
            with open(node.viewpointsFile, 'w') as f:
                f.write(json.dumps(sfmData, indent=4))
                # python3: json.dumps(node.viewpoints, f, indent=4)

    def buildCommandLine(self, chunk):
        cmd = desc.CommandLineNode.buildCommandLine(self, chunk)
        if len(chunk.node.viewpoints):
            cmd += ' --jsonFile ' + chunk.node.viewpointsFile
        return cmd

    def processChunk(self, chunk):
        self.createViewpointsFile(chunk.node)
        desc.CommandLineNode.processChunk(self, chunk)

