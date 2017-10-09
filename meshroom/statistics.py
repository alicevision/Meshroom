#!/usr/bin/env python3
import argparse
import os
from pprint import pprint
from collections import Iterable, defaultdict

from meshroom.core import graph as pg


def addPlots(curves, title, fileObj):
    if not curves:
        return

    import matplotlib.pyplot as plt, mpld3

    fig = plt.figure()
    ax = fig.add_subplot(111, axisbg='#EEEEEE')
    ax.grid(color='white', linestyle='solid')

    for curveName, curve in curves:
        if not isinstance(curve[0], pg.basestring):
            ax.plot(curve, label=curveName)
    ax.legend()
    # plt.ylim(0, 100)
    plt.title(title)

    mpld3.save_html(fig, fileObj)
    plt.close(fig)


parser = argparse.ArgumentParser(description='Query the status of nodes in a Graph of processes.')
parser.add_argument('graphFile', metavar='GRAPHFILE.mg', type=str,
                    help='Filepath to a graph file.')
parser.add_argument('--node', metavar='NODE_NAME', type=str,
                    help='Process the node alone.')
parser.add_argument('--graph', metavar='NODE_NAME', type=str,
                    help='Process the node and all previous nodes needed.')
parser.add_argument('--exportHtml', metavar='FILE', type=str,
                    help='Filepath to the output html file.')
parser.add_argument("--verbose", help="Print full status information",
                    action="store_true")

args = parser.parse_args()

if not os.path.exists(args.graphFile):
    print('ERROR: No graph file "{}".'.format(args.node, args.graphFile))
    exit(-1)

graph = pg.loadGraph(args.graphFile)

graph.update()
graph.updateStatisticsFromCache()

nodes = []
if args.node:
    if args.node not in graph.nodes.keys():
        print('ERROR: node "{}" does not exist in file "{}".'.format(args.node, args.graphFile))
        exit(-1)
    nodes = [graph.node(args.node)]
else:
    startNodes = None
    if args.graph:
        startNodes = [graph.node(args.graph)]
    nodes = graph.dfsNodesOnFinish(startNodes=startNodes)

for node in nodes:
    print('{}: {}'.format(node.name, node.statistics.toDict()))

if args.exportHtml:
    with open(args.exportHtml, 'w') as fileObj:
        for node in nodes:
            for curves in (node.statistics.computer.curves, node.statistics.process.curves):
                exportCurves = defaultdict(list)
                for name, curve in curves.items():
                    s = name.split('.')
                    figName = s[0]
                    curveName = ''.join(s[1:])
                    exportCurves[figName].append((curveName, curve))

                for name, curves in exportCurves.items():
                    addPlots(curves, name, fileObj)
