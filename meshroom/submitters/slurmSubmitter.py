#!/usr/bin/env python
# coding:utf-8

import os
import json


from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

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

    def start(self, node):

        nbFrames = node.size
        arguments = {}
        parallelArgs = ''
        print('node: ', node.name)
        if node.isParallelized:
            pass
            #blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            #parallelArgs = ' --iteration @start'
            #arguments.update({'start': 0, 'end': nbBlocks - 1, 'step': 1})

        #command='{exe} --node {nodeName} "{meshroomFile}" {parallelArgs} --extern'.format(exe='meshroom_compute', nodeName=node.name, meshroomFile=meshroomFile, parallelArgs=parallelArgs),

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
                    vertex.pid = 1
                    self.start(vertex.node)
                    somethingFound = True
            
            if somethingFound == False:
                break

        return True
