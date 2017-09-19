from nose.tools import *

from meshroom import processGraph as pg


def test_depth():
    graph = pg.Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')

    graph.addEdges(
        (tA.output, tB.input),
        (tB.output, tC.input)
        )

    assert_equal(tA.getDepth(), 1)
    assert_equal(tB.getDepth(), 2)
    assert_equal(tC.getDepth(), 3)


if __name__ == '__main__':
    test_depth()
