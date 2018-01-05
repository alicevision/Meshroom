#!/usr/bin/env python
# coding:utf-8

import os

import simpleFarm
from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter


class SimpleFarmSubmitter(BaseSubmitter):
    MESHROOM_PACKAGE = os.environ.get('REZ_USED_REQUEST', '')

    BASE_REQUIREMENTS = ['mikrosRender', '!RenderLow', '!Wkst_OS', '!"vfxpc1*"', '!"vfxpc??"']
    ENGINE = ''
    DEFAULT_TAGS = {'prod': ''}

    def __init__(self, parent=None):
        super(SimpleFarmSubmitter, self).__init__(name='SimpleFarm', parent=parent)
        self.engine = os.environ.get('MESHROOM_SIMPLEFARM_ENGINE', 'tractor')
        self.share = os.environ.get('MESHROOM_SIMPLEFARM_SHARE', 'vfx')
        self.prod = os.environ.get('PROD', 'mvg')

    def createTask(self, meshroomFile, node):
        tags = self.DEFAULT_TAGS.copy()  # copy to not modify default tags
        nbFrames = node.size
        arguments = {}
        parallelArgs = ''
        print('node: ', node.name)
        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            parallelArgs = ' --iteration @start'
            arguments.update({'start': 0, 'end': nbBlocks - 1, 'step': 1})

        tags['nbFrames'] = nbFrames
        tags['prod'] = self.prod
        allRequirements = list(self.BASE_REQUIREMENTS)
        if node.nodeDesc.cpu == Level.INTENSIVE:
            allRequirements.extend(['"RenderHigh*"', '@.nCPUs>20'])
        if node.nodeDesc.gpu != Level.NONE:
            allRequirements.extend(['!"*loc*"', 'Wkst'])
        if node.nodeDesc.ram == Level.INTENSIVE:
            allRequirements.append('@.mem>30')

        task = simpleFarm.Task(
            name=node.nodeType,
            command='meshroom_compute --node {nodeName} "{meshroomFile}" {parallelArgs} --extern'.format(
                nodeName=node.name, meshroomFile=meshroomFile, parallelArgs=parallelArgs),
            tags=tags,
            rezPackages=[self.MESHROOM_PACKAGE],
            requirements={'service': ','.join(allRequirements)},
            **arguments)
        return task

    def submit(self, nodes, edges, filepath):
        name = os.path.splitext(os.path.basename(filepath))[0] + ' [Meshroom]'
        comment = filepath
        nbFrames = max([node.size for node in nodes])

        mainTags = {
            'prod': self.prod,
            'nbFrames': str(nbFrames),
            'comment': comment,
        }

        # Create Job Graph
        job = simpleFarm.Job(name, tags=mainTags)

        nodeNameToTask = {}

        for node in nodes:
            task = self.createTask(filepath, node)
            job.addTask(task)
            nodeNameToTask[node.name] = task

        for u, v in edges:
            nodeNameToTask[u.name].dependsOn(nodeNameToTask[v.name])

        if self.engine == 'tractor-dummy':
            job.submit(share=self.share, engine='tractor', execute=True)
            return True
        else:
            res = job.submit(share=self.share, engine=self.engine)
            return len(res) > 0
