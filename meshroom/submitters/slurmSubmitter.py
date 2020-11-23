
#!/usr/bin/env python
# coding:utf-8

import os
import json
import subprocess

from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(currentDir))

class Vertex:

    def __init__(self, node):
       self.pid = -1
       self.node = node
       self.depends = list()

class SlurmSubmitter(BaseSubmitter):

    def __init__(self, parent=None):
        super(SlurmSubmitter, self).__init__(name='Slurm', parent=parent)
        self.vertices = list()
        self.verticesByNode = dict()

    def start(self, node, dependencies, meshroomFile):

        nbFrames = node.size
        arguments = {}
        parallelArgs = ''

        binary = os.path.join(binDir, 'bin/meshroom_compute')
        bash_content = os.path.join(currentDir, 'slurmCommand.sh')
        jobNameParameter = "--job-name=%s" % node.name
        dependenciesString = ""

        print(node.name)
        
        command = [
            "sbatch",
            "--parsable",
            jobNameParameter,
        ]

        if (len(dependencies) > 0):
            dependenciesString = "--dependency=afterany"
            for dependency in dependencies:
                dependenciesString = "%s:%d" % (dependenciesString, dependency.pid)
            command.append(dependenciesString)

        if node.nodeDesc.gpu.name != "NONE":
            command.append("--partition=gpu")
            command.append("--gres=gpu:1")

        countCores=12
        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            
            if nbBlocks > 1:
                command.append("--array=1-%d" % nbBlocks)
                countCores = 1
        
        command.append("--cpus-per-task=%d" % countCores)

        additional = [
            bash_content,
            binary,
            node.name,
            meshroomFile,
            str(countCores)
        ]
            
        returnString = subprocess.check_output(command + additional)
        returnId = int(returnString)

        return returnId

    def submit(self, nodes, edges, filepath):

        #build a list of nodes with dependencies
        for item in nodes:
            v = Vertex(item)
            self.vertices.append(v)
            self.verticesByNode[item] = v

        #set dependencies
        for edge in edges:
            node = self.verticesByNode[edge[0]]
            dependency = self.verticesByNode[edge[1]]
            node.depends.append(dependency)

        #While all the graph is not submitted
        while True:

            #Try to find a node with all its dependencies submitted
            somethingFound = False

            for vertex in self.vertices:

                #check if vertex was already launched
                if vertex.pid >= 0:
                    continue
                
                #check That all dependency were launched
                valid = True
                for dependency in vertex.depends:
                    if dependency.pid < 0:
                        valid = False
                        break
                
                #launch
                if valid:
                    vertex.pid = self.start(vertex.node, vertex.depends, filepath)
                    somethingFound = True
            
            if somethingFound == False:
                break

        return True
