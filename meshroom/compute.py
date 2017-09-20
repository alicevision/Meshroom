#!/usr/bin/env python3
import argparse

from meshroom.processGraph import graph as pg

parser = argparse.ArgumentParser(description='Execute a Graph of processes.')
parser.add_argument('graphFile', metavar='GRAPHFILE.mg', type=str,
                    help='Filepath to a graph file.')
parser.add_argument('--node', metavar='NODE_NAME', type=str,
                    help='Process the node alone.')
parser.add_argument('--graph', metavar='NODE_NAME', type=str,
                    help='Process the node and all previous nodes needed.')
parser.add_argument("--force", help="Force recompute",
                    action="store_true")

args = parser.parse_args()

# graph = pg.Graph('bashTest')
# ls = graph.addNewNode('Ls', input='/tmp')
# appendText = graph.addNewNode('AppendText', inputText='plop')
# graph.addEdge(ls.output, appendText.input)
## graph.save(args.graphFile)

graph = pg.loadGraph(args.graphFile)
graph.update()

if args.node:
    # Execute the node
    node = graph.nodes[args.node]
    if node.isAlreadySubmitted():
        print('Error: Node is already submitted with status "{}"'.format(node.status.status.name))
        exit(-1)
    if args.force or node.status.status != pg.Status.SUCCESS:
        node.process()
else:
    startNodes = None
    if args.graph:
        startNodes = [graph.nodes[args.graph]]
    pg.execute(graph, startNodes=startNodes, force=args.force)

