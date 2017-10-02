from meshroom.processGraph.graph import Graph


def test_depth():
    graph = Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')

    graph.addEdges(
        (tA.output, tB.input),
        (tB.output, tC.input)
        )

    assert tA.getDepth() == 1
    assert tB.getDepth() == 2
    assert tC.getDepth() == 3


if __name__ == '__main__':
    test_depth()
