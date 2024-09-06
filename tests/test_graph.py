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

    flowEdges = graph.flowEdges()
    flowEdgesRes = [(tB, tA),
                    (tD, tB),
                    (tC, tB),
                    (tE, tD),
                    (tE, tC),
                    ]
    assert set(flowEdgesRes) == set(flowEdges)

    assert len(graph._nodesMinMaxDepths) == len(graph.nodes)
    for node, (minDepth, maxDepth) in graph._nodesMinMaxDepths.items():
        assert node.depth == maxDepth


def test_graph_reverse_dfsOnDiscover():
    graph = Graph('Test dfsOnDiscover(reverse=True)')

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
    nodes = graph.dfsOnDiscover(startNodes=[A], reverse=True)[0]
    assert set(nodes) == {A, B, D, C, E, F}
    # Get all nodes from B
    nodes = graph.dfsOnDiscover(startNodes=[B], reverse=True)[0]
    assert set(nodes) == {B, D, C, E, F}
    # Get all nodes of type AppendText from B
    nodes = graph.dfsOnDiscover(startNodes=[B], filterTypes=['AppendText'], reverse=True)[0]
    assert set(nodes) == {B, D, C, F}
    # Get all nodes from C (order guaranteed)
    nodes = graph.dfsOnDiscover(startNodes=[C], reverse=True)[0]
    assert nodes == [C, E, F]
    # Get all nodes
    nodes = graph.dfsOnDiscover(reverse=True)[0]
    assert set(nodes) == {A, B, C, D, E, F}


def test_graph_dfsOnDiscover():
    graph = Graph('Test dfsOnDiscover(reverse=False)')

    #    ------------\
    #   /   ~ C - E - F
    # A - B
    #      ~ D
    #    G

    G = graph.addNewNode('Ls', input='/tmp')
    A = graph.addNewNode('Ls', input='/tmp')
    B = graph.addNewNode('AppendText', inputText=A.output)
    C = graph.addNewNode('AppendText', inputText=B.output)
    D = graph.addNewNode('AppendText', input=G.output, inputText=B.output)
    E = graph.addNewNode('Ls', input=C.output)
    F = graph.addNewNode('AppendText', input=A.output, inputText=E.output)

    # Get all nodes from A (use set, order not guaranteed)
    nodes = graph.dfsOnDiscover(startNodes=[A], reverse=False)[0]
    assert set(nodes) == {A}
    # Get all nodes from D
    nodes = graph.dfsOnDiscover(startNodes=[D], reverse=False)[0]
    assert set(nodes) == {A, B, D, G}
    # Get all nodes from E
    nodes = graph.dfsOnDiscover(startNodes=[E], reverse=False)[0]
    assert set(nodes) == {A, B, C, E}
    # Get all nodes from F
    nodes = graph.dfsOnDiscover(startNodes=[F], reverse=False)[0]
    assert set(nodes) == {A, B, C, E, F}
    # Get all nodes of type AppendText from C
    nodes = graph.dfsOnDiscover(startNodes=[C], filterTypes=['AppendText'], reverse=False)[0]
    assert set(nodes) == {B, C}
    # Get all nodes from D (order guaranteed)
    nodes = graph.dfsOnDiscover(startNodes=[D], longestPathFirst=True, reverse=False)[0]
    assert nodes == [D, B, A, G]
    # Get all nodes
    nodes = graph.dfsOnDiscover(reverse=False)[0]
    assert set(nodes) == {A, B, C, D, E, F, G}


def test_graph_nodes_sorting():
    graph = Graph('')

    ls0 = graph.addNewNode('Ls')
    ls1 = graph.addNewNode('Ls')
    ls2 = graph.addNewNode('Ls')

    assert graph.nodesOfType('Ls', sortedByIndex=True) == [ls0, ls1, ls2]

    graph = Graph('')
    # 'Random' creation order (what happens when loading a file)
    ls2 = graph.addNewNode('Ls', name='Ls_2')
    ls0 = graph.addNewNode('Ls', name='Ls_0')
    ls1 = graph.addNewNode('Ls', name='Ls_1')

    assert graph.nodesOfType('Ls', sortedByIndex=True) == [ls0, ls1, ls2]


def test_duplicate_nodes():
    """
    Test nodes duplication.
    """

    # n0 -- n1 -- n2
    #   \          \
    #    ---------- n3

    g = Graph('')
    n0 = g.addNewNode('Ls', input='/tmp')
    n1 = g.addNewNode('Ls', input=n0.output)
    n2 = g.addNewNode('Ls', input=n1.output)
    n3 = g.addNewNode('AppendFiles', input=n1.output, input2=n2.output)

    # duplicate from n1
    nodes_to_duplicate, _ = g.dfsOnDiscover(startNodes=[n1], reverse=True, dependenciesOnly=True)
    nMap = g.duplicateNodes(srcNodes=nodes_to_duplicate)
    for s, duplicated in nMap.items():
        for d in duplicated:
            assert s.nodeType == d.nodeType

    # check number of duplicated nodes and that every parent node has been duplicated once
    assert len(nMap) == 3 and all([len(nMap[i]) == 1 for i in nMap.keys()])

    # check connections
    # access directly index 0 because we know there is a single duplicate for each parent node
    assert nMap[n1][0].input.getLinkParam() == n0.output
    assert nMap[n2][0].input.getLinkParam() == nMap[n1][0].output
    assert nMap[n3][0].input.getLinkParam() == nMap[n1][0].output
    assert nMap[n3][0].input2.getLinkParam() == nMap[n2][0].output
