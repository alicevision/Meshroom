#!/usr/bin/env python
# coding:utf-8

import os

import fireworks
from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter


class FireworksSubmitter(BaseSubmitter):
    MESHROOM_PACKAGE = os.environ.get('REZ_USED_REQUEST', '')

    def __init__(self, parent=None):
        super(SimpleFarmSubmitter, self).__init__(name='Fireworks', parent=parent)

    def createFirework(self, meshroomFile, node):
        nbFrames = node.size
        print('node: ', node.name)
        works = []
        nbBlocks = 1
        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
        for i in range(nbBlocks):
            if node.isParallelized:
                parallelArgs = ' --iteration {}'.format(i)
            else:
                parallelArgs = ''

            command = 'meshroom_compute --node {nodeName} "{meshroomFile}" {parallelArgs} --extern'.format(
                    nodeName=node.name, meshroomFile=meshroomFile, parallelArgs=parallelArgs)
            work = fireworks.Firework(
                ScriptTask.from_str(command),
                name=node.nodeType,
                **arguments)
            works.append(work)

        return works

    def submit(self, nodes, edges, filepath):
        launchpad = fireworks.LaunchPad()
        name = os.path.splitext(os.path.basename(filepath))[0] + ' [Meshroom]'
        comment = filepath
        nbFrames = max([node.size for node in nodes])

        allWorks = []
        nodeNameToWorks = {}

        for node in nodes:
            works = self.createFirework(filepath, node)
            allWorks.extend(works)
            nodeNameToWorks[node.name] = works

        allDependencies = {}
        for u, v in edges:
            for uWork in nodeNameToWorks[u.name]:
                if uWork in dependencies:
                    dependencies[uWork].extend(nodeNameToWorks[v.name])
                else:
                    dependencies[uWork] = nodeNameToWorks[v.name]

        print('nodeNameToWorks:', nodeNameToWorks)
        print('dependencies:', dependencies)

        # Create Job Graph
        workflow = fireworks.Workflow(allWorks, allDependencies)

        launchpad.add_wf(workflow)
        fireworks.core.rocket_launcher.launch_rocket(launchpad)

        return True


