from meshroom.core.graph import Graph


def test_depth():
    graph = Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')

    graph.addEdges(
        (tA.output, tB.input),
        (tB.output, tC.input)
        )

    assert tA.depth == 1
    assert tB.depth == 2
    assert tC.depth == 3


if __name__ == '__main__':
    test_depth()
