#!/usr/bin/env python3
import processGraph as pg

import os
import sys

import argparse
from pprint import pprint

    
parser = argparse.ArgumentParser(description='Query the status of nodes in a Graph of processes.')
parser.add_argument('graphFile', metavar='GRAPHFILE.mg', type=str,
                    help='Filepath to a graph file.')
parser.add_argument('--node', metavar='NODE_NAME', type=str,
                    help='Process the node alone.')
parser.add_argument('--graph', metavar='NODE_NAME', type=str,
                    help='Process the node and all previous nodes needed.')
parser.add_argument("--verbose", help="Print full status information",
                    action="store_true")

args = parser.parse_args()

if not os.path.exists(args.graphFile):
    print('ERROR: No graph file "{}".'.format(args.node, args.graphFile))
    exit(-1)

graph = pg.loadGraph(args.graphFile)

graph.update()

if args.node:
    if args.node not in graph.nodes:
        print('ERROR: node "{}" does not exist in file "{}".'.format(args.node, args.graphFile))
        exit(-1)
    node = graph.nodes[args.node]
    print('{}: {}'.format(node.name, node.status.status.name))
    if args.verbose:
        print('statusFile: ', node.statusFile())
        pprint(node.status.toDict())
else:
    startNodes = None
    if args.graph:
        startNodes = [graph.nodes[args.graph]]
    nodes = graph.dfsNodesOnFinish(startNodes=startNodes)
    for n in nodes:
        print('{}: {}'.format(node.name, node.status.status.name))
    if args.verbose:
        pprint([n.status.toDict() for n in nodes])

