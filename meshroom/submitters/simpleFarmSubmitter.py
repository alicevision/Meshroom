#!/usr/bin/env python

import os
import json
import logging
import getpass
import re

import simpleFarm
from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

class SimpleFarmSubmitter(BaseSubmitter):

    filepath = os.environ.get('SIMPLEFARMCONFIG', os.path.join(currentDir, 'tractorConfig.json'))
    config = json.load(open(filepath))

    reqPackages = []
    environment = {}
    ENGINE = ''
    DEFAULT_TAGS = {'prod': ''}
    REZ_DELIMITER_PATTERN = re.compile(r"-|==|>=|>|<=|<")

    def __init__(self, parent=None):
        super().__init__(name='SimpleFarm', parent=parent)
        self.engine = os.environ.get('MESHROOM_SIMPLEFARM_ENGINE', 'tractor')
        self.share = os.environ.get('MESHROOM_SIMPLEFARM_SHARE', 'vfx')
        self.prod = os.environ.get('PROD', 'mvg')
        if 'REZ_USED_REQUEST' in os.environ:
            requestPackages = os.environ.get('REZ_USED_REQUEST', '').split()
            resolvedPackages = os.environ.get('REZ_RESOLVE', '').split()
            resolvedVersions = {}
            for r in resolvedPackages:
                # remove implicit packages
                if r.startswith('~'):
                    continue
                # logging.info('REZ: {}'.format(str(r)))
                name, version = self.REZ_DELIMITER_PATTERN.split(r, maxsplit=1)
                # logging.info('    v: {}'.format(str(v)))
                resolvedVersions[name] = version
            requestPackageNames = set()  # Use set to remove duplicates
            for p in requestPackages:
                if p.startswith('~'):
                    continue
                v = self.REZ_DELIMITER_PATTERN.split(p, maxsplit=1)
                requestPackageNames.add(v[0])
            for p in requestPackageNames:
                # Use "==" to guarantee that the job uses the exact same version
                # as the environment where Meshroom was launched.
                self.reqPackages.append(f"{p}=={resolvedVersions[p]}")
            logging.debug(f'REZ Packages: {str(self.reqPackages)}')
        elif 'REZ_MESHROOM_VERSION' in os.environ:
            self.reqPackages = [f"meshroom-{os.environ.get('REZ_MESHROOM_VERSION', '')}"]
        else:
            self.reqPackages = None

        if 'REZ_DEV_PACKAGES_ROOT' in os.environ:
            self.environment['REZ_DEV_PACKAGES_ROOT'] = os.environ['REZ_DEV_PACKAGES_ROOT']

        if 'REZ_PROD_PACKAGES_PATH' in os.environ:
            self.environment['REZ_PROD_PACKAGES_PATH'] = os.environ['REZ_PROD_PACKAGES_PATH']

        if 'PROD' in os.environ:
            self.environment['PROD'] = os.environ['PROD']

        if 'PROD_ROOT' in os.environ:
            self.environment['PROD_ROOT'] = os.environ['PROD_ROOT']

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
        allRequirements = set()
        allRequirements.update(self.config['CPU'].get(node.nodeDesc.cpu.name, []))
        allRequirements.update(self.config['RAM'].get(node.nodeDesc.ram.name, []))
        allRequirements.update(self.config['GPU'].get(node.nodeDesc.gpu.name, []))

        executable = 'meshroom_compute' if self.reqPackages else os.path.join(binDir, 'meshroom_compute')
        taskCommand = f"{executable} --node {node.name} \"{meshroomFile}\" {parallelArgs} --extern"
        task = simpleFarm.Task(
            name=node.name, command=taskCommand, tags=tags, rezPackages=self.reqPackages,
            requirements={'service': str(','.join(allRequirements))}, **arguments)
        return task

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}"):

        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)

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
                environment=self.environment,
                user=os.environ.get('FARM_USER', os.environ.get('USER', getpass.getuser())),
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
