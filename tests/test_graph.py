from meshroom.core.graph import Graph


def test_depth():
    graph = Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')

    graph.addEdges(
        (tA.output, tB.input),
        (tB.output, tC.input),
        )

    assert tA.depth == 0
    assert tB.depth == 1
    assert tC.depth == 2


def test_depth_diamond_graph():
    graph = Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')
    tD = graph.addNewNode('AppendFiles')

    graph.addEdges(
        (tA.output, tB.input),
        (tA.output, tC.input),
        (tB.output, tD.input),
        (tC.output, tD.input2),
        )

    assert tA.depth == 0
    assert tB.depth == 1
    assert tC.depth == 1
    assert tD.depth == 2

    nodes, edges = graph.dfsOnFinish()
    assert len(nodes) == 4
    assert nodes[0] == tA
    assert nodes[-1] == tD
    assert len(edges) == 4

    nodes, edges = graph.dfsOnFinish(startNodes=[tD])
    assert len(nodes) == 4
    assert nodes[0] == tA
    assert nodes[-1] == tD
    assert len(edges) == 4

    nodes, edges = graph.dfsOnFinish(startNodes=[tB])
    assert len(nodes) == 2
    assert nodes[0] == tA
    assert nodes[-1] == tB
    assert len(edges) == 1


def test_depth_diamond_graph2():
    graph = Graph('Tests tasks depth')

    tA = graph.addNewNode('Ls', input='/tmp')
    tB = graph.addNewNode('AppendText', inputText='echo B')
    tC = graph.addNewNode('AppendText', inputText='echo C')
    tD = graph.addNewNode('AppendText', inputText='echo D')
    tE = graph.addNewNode('AppendFiles')
    #         C
    #       /   \
    #  /---/---->\
    # A -> B ---> E
    #      \     /
    #       \   /
    #         D
    graph.addEdges(
        (tA.output, tB.input),
        (tB.output, tC.input),
        (tB.output, tD.input),

        (tA.output, tE.input),
        (tB.output, tE.input2),
        (tC.output, tE.input3),
        (tD.output, tE.input4),
        )

    assert tA.depth == 0
    assert tB.depth == 1
    assert tC.depth == 2
    assert tD.depth == 2
    assert tE.depth == 3

    nodes, edges = graph.dfsOnFinish()
    assert len(nodes) == 5
    assert nodes[0] == tA
    assert nodes[-1] == tE
    assert len(edges) == 7

    nodes, edges = graph.dfsOnFinish(startNodes=[tE])
    assert len(nodes) == 5
    assert nodes[0] == tA
    assert nodes[-1] == tE
    assert len(edges) == 7

    nodes, edges = graph.dfsOnFinish(startNodes=[tD])
    assert len(nodes) == 3
    assert nodes[0] == tA
    assert nodes[1] == tB
    assert nodes[2] == tD
    assert len(edges) == 2

    nodes, edges = graph.dfsOnFinish(startNodes=[tB])
    assert len(nodes) == 2
    assert nodes[0] == tA
    assert nodes[-1] == tB
    assert len(edges) == 1


if __name__ == '__main__':
    test_depth()
    test_depth_diamond_graph()
