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
    desc.IntParam(name="viewId", label="Id", description="Image UID", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="poseId", label="Pose Id", description="Pose Id", value=-1, uid=[0], range=(0, 200, 1)),
    desc.File(name="path", label="Image Path", description="Image Filepath", value="", uid=[0, 1]),
    desc.IntParam(name="intrinsicId", label="Intrinsic", description="Internal Camera Parameters", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="rigId", label="Rig", description="Rig Parameters", value=-1, uid=[0], range=(0, 200, 1)),
    desc.IntParam(name="subPoseId", label="Rig Sub-Pose", description="Rig Sub-Pose Parameters", value=-1, uid=[0], range=(0, 200, 1)),
]

Intrinsic = [
    desc.IntParam(name="intrinsicId", label="Id", description="Intrinsic UID", value=-1, uid=[0], range=(0, 200, 1)),
    desc.FloatParam(name="pxInitialFocalLength", label="Initial Focal Length", description="Initial Guess on the Focal Length", value=-1.0, uid=[0], range=(0.0, 200.0, 1.0)),
    desc.FloatParam(name="pxFocalLength", label="Focal Length", description="Known/Calibrated Focal Length", value=-1.0, uid=[0], range=(0.0, 200.0, 1.0)),
    desc.ChoiceParam(name="type", label="Camera Type", description="Camera Type", value="", values=['', 'pinhole', 'radial1', 'radial3', 'brown', 'fisheye4'], exclusive=True, uid=[0]),
    # desc.StringParam(name="deviceMake", label="Make", description="Camera Make", value="", uid=[]),
    # desc.StringParam(name="deviceModel", label="Model", description="Camera Model", value="", uid=[]),
    # desc.StringParam(name="sensorWidth", label="Sensor Width", description="Camera Sensor Width", value="", uid=[0]),
    desc.IntParam(name="width", label="Width", description="Image Width", value=0, uid=[], range=(0, 10000, 1)),
    desc.IntParam(name="height", label="Height", description="Image Height", value=0, uid=[], range=(0, 10000, 1)),
    desc.StringParam(name="serialNumber", label="Serial Number", description="Device Serial Number (camera and lens combined)", value="", uid=[]),
    desc.GroupAttribute(name="principalPoint", label="Principal Point", description="", groupDesc=[
        desc.IntParam(name="x", label="x", description="", value=0, uid=[], range=(0, 10000, 1)),
        desc.IntParam(name="y", label="y", description="", value=0, uid=[], range=(0, 10000, 1)),
        ]),
    desc.ListAttribute(
            name="distortionParams",
            elementDesc=desc.FloatParam(name="p", label="", description="", value=0.0, uid=[0], range=(-0.1, 0.1, 0.01)),
            label="Distortion Params",
            description="Distortion Parameters",
        ),
]


class CameraInit(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_cameraInit {allParams}'

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
            name='defaultIntrinsic',
            label='Default Intrinsic',
            description='''Intrinsic K matrix "f;0;ppx;0;f;ppy;0;0;1".''',
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
            value='{cache}/{nodeType}/{uid0}/cameraInit.sfm',
            uid=[],
        ),
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

            # Reload result of aliceVision_cameraInit
            cameraInitSfM = localCmdVars['outputValue']
            jsonData = open(cameraInitSfM, 'r').read()
            data = json.loads(jsonData)

            intrinsicsKeys = [i.name for i in Intrinsic]
            intrinsics = [{k: v for k, v in item.items() if k in intrinsicsKeys} for item in data.get("intrinsics", [])]
            for intrinsic in intrinsics:
                pp = intrinsic['principalPoint']
                intrinsic['principalPoint'] = {}
                intrinsic['principalPoint']['x'] = pp[0]
                intrinsic['principalPoint']['y'] = pp[1]
            # print('intrinsics:', intrinsics)
            viewsKeys = [v.name for v in Viewpoint]
            views = [{k: v for k, v in item.items() if k in viewsKeys} for item in data.get("views", [])]
            # print('views:', views)

            with GraphModification(node.graph):
                node.viewpoints.value = views
                node.intrinsics.value = intrinsics
                node.attribute("_viewpointsUid").value = node.viewpoints.uid(1)

        except Exception:
            logging.warning('CameraInit: Error on updateInternals of node "{}".'.format(node.name))
            raise
        finally:
            node._cmdVars = origCmdVars
            shutil.rmtree(tmpCache)

    def createViewpointsFile(self, node):
        if node.viewpoints:
            intrinsics = node.intrinsics.getPrimitiveValue(exportDefault=True)
            for intrinsic in intrinsics:
                intrinsic['principalPoint'] = [intrinsic['principalPoint']['x'], intrinsic['principalPoint']['y']]
            sfmData = {
                "version": [1, 0, 0],
                "views": node.viewpoints.getPrimitiveValue(exportDefault=False),
                "intrinsics": intrinsics,
                "featureFolder": "",
                "matchingFolder": "",
            }
            node.viewpointsFile = '{cache}/{nodeType}/{uid0}/viewpoints.json'.format(**node._cmdVars)
            with open(node.viewpointsFile, 'w') as f:
                f.write(json.dumps(sfmData, indent=4))
                # python3: json.dumps(node.viewpoints, f, indent=4)

    def createViewpointsFile_old(self, node):
        """
        Temporary compatibility method.
        """
        if node.viewpoints:
            sfmData = {
                "resources": [v.get("path", "") for v in node.viewpoints.getPrimitiveValue(exportDefault=False)],
            }
            node.viewpointsFile = '{cache}/{nodeType}/{uid0}/viewpoints.json'.format(**node._cmdVars)
            with open(node.viewpointsFile, 'w') as f:
                f.write(json.dumps(sfmData, indent=4))
                # python3: json.dumps(node.viewpoints, f, indent=4)

    def buildCommandLine(self, chunk):
        cmd = desc.CommandLineNode.buildCommandLine(self, chunk)
        if len(chunk.node.viewpoints):
            cmd += ' --input ' + chunk.node.viewpointsFile
        return cmd

    def processChunk(self, chunk):
        self.createViewpointsFile(chunk.node)
        desc.CommandLineNode.processChunk(self, chunk)

