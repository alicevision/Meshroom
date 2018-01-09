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


def test_transitive_reduction():

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
        (tA.output, tE.input),

        (tA.output, tB.input),
        (tB.output, tC.input),
        (tB.output, tD.input),

        (tB.output, tE.input4),
        (tC.output, tE.input3),
        (tD.output, tE.input2),
        )
    edgesScore = graph.dfsMaxEdgeLength()

    flowEdges = graph.flowEdges()
    flowEdgesRes = [(tB, tA),
                    (tD, tB),
                    (tC, tB),
                    (tE, tD),
                    (tE, tC),
                    ]
    assert set(flowEdgesRes) == set(flowEdges)

    depthPerNode = graph.minMaxDepthPerNode()
    assert len(depthPerNode) ==  len(graph.nodes)
    for node, (minDepth, maxDepth) in depthPerNode.iteritems():
        assert node.depth == maxDepth


def test_graph_reverse_dfs():
    graph = Graph('Test reverse DFS')

    #    ------------\
    #   /   ~ C - E - F
    # A - B
    #      ~ D

    A = graph.addNewNode('Ls', input='/tmp')
    B = graph.addNewNode('AppendText', inputText=A.output)
    C = graph.addNewNode('AppendText', inputText=B.output)
    D = graph.addNewNode('AppendText', inputText=B.output)
    E = graph.addNewNode('Ls', input=C.output)
    F = graph.addNewNode('AppendText', input=A.output, inputText=E.output)

    # Get all nodes from A (use set, order not guaranteed)
    nodes = graph.nodesFromNode(A)[0]
    assert set(nodes) == {A, B, D, C, E, F}
    # Get all nodes from B
    nodes = graph.nodesFromNode(B)[0]
    assert set(nodes) == {B, D, C, E, F}
    # Get all nodes of type AppendText from B
    nodes = graph.nodesFromNode(B, filterType='AppendText')[0]
    assert set(nodes) == {B, D, C, F}
    # Get all nodes from C (order guaranteed)
    nodes = graph.nodesFromNode(C)[0]
    assert nodes == [C, E, F]
