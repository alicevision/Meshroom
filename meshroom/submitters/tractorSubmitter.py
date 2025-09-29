#!/usr/bin/env python

import re
import os
import json
import getpass
import logging

from meshroom.core.submitter import BaseSubmitter

import meshroom.submitters.tractorApi.api as tractorApi


currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

REZ_DELIMITER_PATTERN = re.compile(r"(-|==|>=|>|<=|<)")


class Config:
    def __init__(self, filepath=None):
        if not filepath:
            filepath = os.environ.get("TRACTORCONFIG", os.path.join(currentDir, 'tractorConfig.json'))
        self.config = json.load(open(filepath))
        self.base = self.config.get('BASE', [])
        self.cpu = self.config.get('CPU', {})
        self.ram = self.config.get('RAM', {})
        self.gpu = self.config.get('GPU', {})


def get_job_packages():
    reqPackages = []
    if 'REZ_REQUEST' in os.environ:
        packages = os.environ.get('REZ_USED_REQUEST', '').split()
        resolvedPackages = os.environ.get('REZ_RESOLVE', '').split()
        resolvedVersions = {}
        for r in resolvedPackages:
            if r.startswith('~'):  # remove implicit packages
                continue
            v = r.split('-')
            if len(v) == 2:
                resolvedVersions[v[0]] = v[1]
            elif len(v) > 2:  # Handle case with multiple hyphen-minus
                resolvedVersions[v[0]] = "-".join(v[1:])
        usedPackages = set()  # Use set to remove duplicates
        for p in packages:
            if p.startswith('~') or p.startswith("!"):
                continue
            v = REZ_DELIMITER_PATTERN.split(p)
            usedPackages.add(v[0])
        for p in usedPackages:
            # Use "==" to make sure we have the same version in the job that the one we have in the env
            # where meshroom is launched
            reqPackages.append("==".join([p, resolvedVersions[p]]))
        logging.debug(f'[DEBUG] REZ Packages: {str(reqPackages)}')
    elif 'REZ_MESHROOM_VERSION' in os.environ:
        reqPackages.append(f"meshroom-{os.environ.get('REZ_MESHROOM_VERSION', '')}")
    return reqPackages


class TractorSubmitter(BaseSubmitter):

    dryRun = False
    config = Config()
    environment = {}
    DEFAULT_TAGS = {'prod': ''}
    
    def __init__(self, parent=None):
        super().__init__(name='Tractor', parent=parent)
        self.share = os.environ.get('MESHROOM_TRACTOR_SHARE', 'vfx')
        self.prod = os.environ.get('PROD', 'mvg')
        self.reqPackages = get_job_packages()
        if 'REZ_DEV_PACKAGES_ROOT' in os.environ:
            self.environment['REZ_DEV_PACKAGES_ROOT'] = os.environ['REZ_DEV_PACKAGES_ROOT']
        if 'REZ_PROD_PACKAGES_PATH' in os.environ:
            self.environment['REZ_PROD_PACKAGES_PATH'] = os.environ['REZ_PROD_PACKAGES_PATH']

    def createTask(self, meshroomFile, node):
        tags = self.DEFAULT_TAGS.copy()  # copy to not modify default tags
        optionalArgs = {}
        parallelArgs = ''
        logging.info('node: ', node.name)
        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            if nbBlocks > 1:  # Is it better like this ?
                parallelArgs = ' --iteration @start'
                optionalArgs.update({'start': 0, 'end': nbBlocks - 1, 'step': 1})
        tags['nbFrames'] = node.size
        tags['prod'] = self.prod
        allRequirements = list()
        allRequirements.extend(self.config.cpu.get(node.nodeDesc.cpu.name, []))
        allRequirements.extend(self.config.ram.get(node.nodeDesc.ram.name, []))
        allRequirements.extend(self.config.gpu.get(node.nodeDesc.gpu.name, []))
        exe = "meshroom_compute" if self.reqPackages else os.path.join(binDir, "meshroom_compute")
        taskCommand = f"{exe} --node {node.name} \"{meshroomFile}\" {parallelArgs} --extern"
        task = tractorApi.Task(
            name=node.name,
            command=taskCommand,
            tags=tags,
            rezPackages=self.reqPackages,
            requirements={'service': str(','.join(allRequirements))},
            **optionalArgs)
        return task

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}"):
        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)
        comment = filepath
        maxNodeSize = max([node.size for node in nodes])
        mainTags = {
            'prod': self.prod,
            'nbFrames': str(maxNodeSize),
            'comment': comment,
        }
        allRequirements = list(self.config.base)

        # Create Job Graph
        job = tractorApi.Job(
            name,
            tags=mainTags,
            requirements={'service': str(','.join(allRequirements))},
            environment=self.environment,
            user=os.environ.get('USER', os.environ.get('FARM_USER', getpass.getuser())),
        )

        nodeNameToTask = {}

        for node in nodes:
            task = self.createTask(filepath, node)
            job.addTask(task)
            nodeNameToTask[node.name] = task

        for u, v in edges:
            nodeNameToTask[u.name].addParents(nodeNameToTask[v.name])

        res = job.submit(share=self.share, dryRun=self.dryRun)
        if self.dryRun:
            return True
        return len(res) > 0
