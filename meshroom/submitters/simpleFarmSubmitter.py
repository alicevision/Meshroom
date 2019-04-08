#!/usr/bin/env python
# coding:utf-8

import os
import json

import simpleFarm
from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

class SimpleFarmSubmitter(BaseSubmitter):
    if 'REZ_MESHROOM_VERSION' in os.environ:
        MESHROOM_PACKAGE = "meshroom-{}".format(os.environ.get('REZ_MESHROOM_VERSION', ''))
    else:
        MESHROOM_PACKAGE = None

    filepath = os.environ.get('SIMPLEFARMCONFIG', os.path.join(currentDir, 'simpleFarmConfig.json'))
    config = json.load(open(filepath))

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
        allRequirements = list()
        allRequirements.extend(self.config['CPU'].get(node.nodeDesc.cpu.name, []))
        allRequirements.extend(self.config['RAM'].get(node.nodeDesc.ram.name, []))
        allRequirements.extend(self.config['GPU'].get(node.nodeDesc.gpu.name, []))

        task = simpleFarm.Task(
            name=node.nodeType,
            command='{exe} --node {nodeName} "{meshroomFile}" {parallelArgs} --extern'.format(
                exe='meshroom_compute' if self.MESHROOM_PACKAGE else os.path.join(binDir, 'meshroom_compute'),
                nodeName=node.name, meshroomFile=meshroomFile, parallelArgs=parallelArgs),
            tags=tags,
            rezPackages=[self.MESHROOM_PACKAGE] if self.MESHROOM_PACKAGE else None,
            requirements={'service': str(','.join(allRequirements))},
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
        allRequirements = list(self.config.get('BASE', []))

        # Create Job Graph
        job = simpleFarm.Job(name,
                tags=mainTags,
                requirements={'service': str(','.join(allRequirements))},
                )

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
