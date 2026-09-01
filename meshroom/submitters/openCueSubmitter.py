#!/usr/bin/env python
# coding:utf-8

from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

import outline

import os
currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

import datetime

class OpenCueSubmitter(BaseSubmitter):
    def __init__(self, parent=None):
        super(OpenCueSubmitter, self).__init__(name='OpenCue', parent=parent)
        self.prod = os.environ.get('PROD', 'mvg')

    def createTask(self, meshroomFile, node, name, dateStr):
        frameRange = "0-0"
        exe = os.path.join(binDir, 'meshroom_compute')
        command = ["echo", "$ALICEVISION_SENSOR_DB", "&&", exe, "--node", node.name, meshroomFile, "--extern", "--cache", "/shots/testing/" + name + "/cache" + dateStr ]

        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            command.append("--iteration #IFRAME#")
            frameRange = "0-" + str(nbBlocks-1)

        task = outline.Layer(node.name, env={}, service="shell", chunk=1, command=command)
        task.set_frame_range(frameRange)

        return task

    def submit(self, nodes, edges, filepath):
        now = datetime.datetime.now()
        dateStr = now.strftime("%Y-%m-%d--%H-%M-%S")

        name = os.path.splitext(os.path.basename(filepath))[0]
        user = 'render'  # str(os.environ['USER'])

        nbFrames = max([node.size for node in nodes])
        job = outline.Outline(name + "--" + dateStr, user=user, frame_range="0-"+str(nbFrames), shot=name, show="testing")
        #job.set_env('ALICEVISION_SENSOR_DB', '/usr/local/meshroom/aliceVision/share/aliceVision/cameraSensors.db', True)
        #job.set_env('ALICEVISION_VOCTREE', '/usr/local/meshroom/aliceVision/share/aliceVision/vlfeat_K80L3.SIFT.tree', True)

        nodeNameToTask = {}

        for node in nodes:
            task = self.createTask(filepath, node, name, dateStr)
            job.add_layer(task)
            nodeNameToTask[node.name] = task

        for u, v in edges:
            nodeNameToTask[u.name].depend_on(nodeNameToTask[v.name], outline.depend.DependType.LayerOnLayer)

        try:
            outline.cuerun.launch(job, use_pycuerun=False)
            return True
        except:
            return False

