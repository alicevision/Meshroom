from meshroom.core.graph import Graph
from meshroom.core.node import Status


def test_depth():
    graph = Graph("Tests tasks depth")

    tA = graph.addNewNode("Ls", input="/tmp")
    tB = graph.addNewNode("AppendText", inputText="echo B")
    tC = graph.addNewNode("AppendText", inputText="echo C")

    tA.output.connectTo(tB.input)
    tB.output.connectTo(tC.input)

    assert tA.depth == 0
    assert tB.depth == 1
    assert tC.depth == 2


def test_transitive_reduction():
    graph = Graph("Tests tasks depth")

    tA = graph.addNewNode("Ls", input="/tmp")
    tB = graph.addNewNode("AppendText", inputText="echo B")
    tC = graph.addNewNode("AppendText", inputText="echo C")
    tD = graph.addNewNode("AppendText", inputText="echo D")
    tE = graph.addNewNode("AppendFiles")
    #         C
    #       /   \
    #  /---/---->\
    # A -> B ---> E
    #      \     /
    #       \   /
    #         D
    tA.output.connectTo(tE.input)
    tA.output.connectTo(tB.input)
    tB.output.connectTo(tC.input)
    tB.output.connectTo(tD.input)
    tB.output.connectTo(tE.input4)
    tC.output.connectTo(tE.input3)
    tD.output.connectTo(tE.input2)

    flowEdges = graph.flowEdges()
    flowEdgesRes = [(tB, tA),
                    (tD, tB),
                    (tC, tB),
                    (tE, tD),
                    (tE, tC),
                    ]
    assert set(flowEdgesRes) == set(flowEdges)

    assert len(graph._nodesMinMaxDepths) == len(graph.nodes)
    for node, (_, maxDepth) in graph._nodesMinMaxDepths.items():
        assert node.depth == maxDepth


def test_graph_nodes_sorting():
    graph = Graph("")

    ls0 = graph.addNewNode("Ls")
    ls1 = graph.addNewNode("Ls")
    ls2 = graph.addNewNode("Ls")

    assert graph.nodesOfType("Ls", sortedByIndex=True) == [ls0, ls1, ls2]

    graph = Graph("")
    # 'Random' creation order (what happens when loading a file)
    ls2 = graph.addNewNode("Ls", name="Ls_2")
    ls0 = graph.addNewNode("Ls", name="Ls_0")
    ls1 = graph.addNewNode("Ls", name="Ls_1")

    assert graph.nodesOfType("Ls", sortedByIndex=True) == [ls0, ls1, ls2]


def test_duplicate_nodes():
    """
    Test nodes duplication.
    """

    # n0 -- n1 -- n2
    #   \          \
    #    ---------- n3

    g = Graph("")
    n0 = g.addNewNode("Ls", input="/tmp")
    n1 = g.addNewNode("Ls", input=n0.output)
    n2 = g.addNewNode("Ls", input=n1.output)
    n3 = g.addNewNode("AppendFiles", input=n1.output, input2=n2.output)

    # Duplicate from n1
    nodes_to_duplicate, _ = g.dfsOnDiscover(startNodes=[n1], reverse=True, dependenciesOnly=True)
    nMap = g.duplicateNodes(srcNodes=nodes_to_duplicate)
    for s, duplicated in nMap.items():
        for d in duplicated:
            assert s.nodeType == d.nodeType

    # Check number of duplicated nodes and that every parent node has been duplicated once
    assert len(nMap) == 3 and \
        all([len(nMap[i]) == 1 for i in nMap.keys()])

    # Check connections
    # Access directly index 0 because we know there is a single duplicate for each parent node
    assert nMap[n1][0].input.inputLink == n0.output
    assert nMap[n2][0].input.inputLink == nMap[n1][0].output
    assert nMap[n3][0].input.inputLink == nMap[n1][0].output
    assert nMap[n3][0].input2.inputLink == nMap[n2][0].output


def test_rename_nodes():
    """
    Test renaming nodes.
    """

    graph = Graph("")
    ls0 = graph.addNewNode("Ls")
    ls1 = graph.addNewNode("Ls")
    ls2 = graph.addNewNode("Ls")

    # Test with empty string
    assert ls0.name == "Ls"
    graph.renameNode(ls0, "")
    assert ls0.name == "Ls"

    # Rename
    graph.renameNode(ls0, "nodels")
    assert ls0.name == "nodels"
    graph.renameNode(ls1, "nodels")
    assert ls1.name == "nodels_1"
    graph.renameNode(ls2, "nodels")
    assert ls2.name == "nodels_2"

    # Check we cannot rename in locked mode
    ls0.setLocked(True)
    assert not graph.renameNode(ls0, "lockedLs")
    assert ls0.name == "nodels"
    ls0.setLocked(False)

    # Check the returned value
    assert graph.renameNode(ls0, "renamedLs")
    assert ls0.name == "renamedLs"
    assert not graph.renameNode(ls0, "")
    assert ls0.name == "renamedLs"


def test_rename_node_with_cache():
    """
    Test that a node with a cache cannot be renamed.
    """
    graph = Graph("")
    ls = graph.addNewNode("Ls")
    assert not ls.hasCache()

    for chunk in ls.getAllChunks():
        chunk._status.status = Status.SUCCESS
    ls._nodeStatus.status = Status.SUCCESS
    assert ls.hasCache()
    assert not graph.renameNode(ls, "cachedLs")
    assert ls.name == "Ls"


def test_rename_node_updates_label():
    """
    Test that the label follows the name when no custom label is set.
    """
    graph = Graph("")
    ls = graph.addNewNode("Ls")
    assert ls.label == "Ls"
    assert ls.defaultLabel == "Ls"

    labelChanges = []
    ls.internalAttributesChanged.connect(lambda: labelChanges.append(ls.label))
    graph.renameNode(ls, "myLs")
    assert ls.label == "myLs"
    assert labelChanges and labelChanges[-1] == "myLs"
    # The default label stays the node type
    assert ls.defaultLabel == "Ls"

    # A custom label is kept after renaming
    ls.internalAttribute("label").value = "Custom"
    graph.renameNode(ls, "otherLs")
    assert ls.label == "Custom"


class TestUniqueNodeName:
    """ Tests for the unique node name generation. """

    def test_free_name_is_kept(self):
        graph = Graph("")
        assert graph._createUniqueNodeName("Ls", set()) == "Ls"

    def test_index_is_added_on_collision(self):
        graph = Graph("")
        assert graph._createUniqueNodeName("Ls", {"Ls"}) == "Ls_1"
        assert graph._createUniqueNodeName("Ls", {"Ls", "Ls_1"}) == "Ls_2"

    def test_first_free_index_is_used(self):
        graph = Graph("")
        assert graph._createUniqueNodeName("Ls", {"Ls", "Ls_2"}) == "Ls_1"

    def test_index_suffix_is_stripped(self):
        graph = Graph("")
        assert graph._createUniqueNodeName("Ls_5", set()) == "Ls"
        assert graph._createUniqueNodeName("Ls_5", {"Ls"}) == "Ls_1"

    def test_non_index_underscore_is_kept(self):
        graph = Graph("")
        assert graph._createUniqueNodeName("My_Ls", set()) == "My_Ls"

    def test_uses_graph_nodes_by_default(self):
        graph = Graph("")
        graph.addNewNode("Ls")
        graph.addNewNode("Ls")
        assert sorted(graph.nodes.keys()) == ["Ls", "Ls_1"]
        assert graph._createUniqueNodeName("Ls") == "Ls_2"


class TestDFS:
    """ Tests for the graph DFS traversal methods. """

    def test_dfs_on_finish_depth_diamond_graph(self):
        graph = Graph("Tests tasks depth (diamond graph)")

        tA = graph.addNewNode("Ls", input="/tmp")
        tB = graph.addNewNode("AppendText", inputText="echo B")
        tC = graph.addNewNode("AppendText", inputText="echo C")
        tD = graph.addNewNode("AppendFiles")

        tA.output.connectTo(tB.input)
        tA.output.connectTo(tC.input)
        tB.output.connectTo(tD.input)
        tC.output.connectTo(tD.input2)

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

    def test_dfs_on_finish_depth_diamond_graph2(self):
        graph = Graph("Tests tasks depth (diamond graph 2)")

        tA = graph.addNewNode("Ls", input="/tmp")
        tB = graph.addNewNode("AppendText", inputText="echo B")
        tC = graph.addNewNode("AppendText", inputText="echo C")
        tD = graph.addNewNode("AppendText", inputText="echo D")
        tE = graph.addNewNode("AppendFiles")
        #         C
        #       /   \
        #  /---/----->\
        # A -> B ---> E
        #      \     /
        #       \   /
        #         D
        tA.output.connectTo(tB.input)
        tB.output.connectTo(tC.input)
        tB.output.connectTo(tD.input)
        tA.output.connectTo(tE.input)
        tB.output.connectTo(tE.input2)
        tC.output.connectTo(tE.input3)
        tD.output.connectTo(tE.input4)

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

    def test_reverse_dfs_on_discover(self):
        graph = Graph("Test dfsOnDiscover(reverse=True)")

        #    ------------\
        #   /   ~ C - E - F
        # A - B
        #      ~ D

        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)
        D = graph.addNewNode("AppendText", inputText=B.output)
        E = graph.addNewNode("Ls", input=C.output)
        F = graph.addNewNode("AppendText", input=A.output, inputText=E.output)

        # Get all nodes from A (use set, order not guaranteed)
        nodes = graph.dfsOnDiscover(startNodes=[A], reverse=True)[0]
        assert set(nodes) == {A, B, D, C, E, F}
        # Get all nodes from B
        nodes = graph.dfsOnDiscover(startNodes=[B], reverse=True)[0]
        assert set(nodes) == {B, D, C, E, F}
        # Get all nodes of type AppendText from B
        nodes = graph.dfsOnDiscover(startNodes=[B], filterTypes=["AppendText"], reverse=True)[0]
        assert set(nodes) == {B, D, C, F}
        # Get all nodes from C (order guaranteed)
        nodes = graph.dfsOnDiscover(startNodes=[C], reverse=True)[0]
        assert nodes == [C, E, F]
        # Get all nodes
        nodes = graph.dfsOnDiscover(reverse=True)[0]
        assert set(nodes) == {A, B, C, D, E, F}

    def test_dfs_on_discover(self):
        graph = Graph("Test dfsOnDiscover(reverse=False)")

        #    ------------\
        #   /   ~ C - E - F
        # A - B
        #      ~ D
        #    G

        G = graph.addNewNode("Ls", input="/tmp")
        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)
        D = graph.addNewNode("AppendText", input=G.output, inputText=B.output)
        E = graph.addNewNode("Ls", input=C.output)
        F = graph.addNewNode("AppendText", input=A.output, inputText=E.output)

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
        nodes = graph.dfsOnDiscover(startNodes=[C], filterTypes=["AppendText"], reverse=False)[0]
        assert set(nodes) == {B, C}
        # Get all nodes from D (order guaranteed)
        nodes = graph.dfsOnDiscover(startNodes=[D], longestPathFirst=True, reverse=False)[0]
        assert nodes == [D, B, A, G]
        # Get all nodes
        nodes = graph.dfsOnDiscover(reverse=False)[0]
        assert set(nodes) == {A, B, C, D, E, F, G}

    def test_no_duplicates_start_node_is_ancestor_of_another(self):
        """
        Test that DFS does not visit the same node more than once when one startNode
        is an ancestor (in the traversal direction) of another startNode.

        Graph:
        A -> B -> C

        Starting DFS (reverse=False, toward roots) from both C and B: visiting C first
        will traverse C -> B -> A. B should not be discovered or finished a second time
        when it is encountered again as a startNode.
        """
        graph = Graph("")

        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)

        nodes, _ = graph.dfsOnFinish(startNodes=[C, B])

        # B must appear exactly once — it is visited when traversing from C, and
        # must NOT be re-visited when it is encountered as a startNode.
        assert len(nodes) == len(set(nodes)), "dfsOnFinish returned duplicate nodes"
        assert len(nodes) == 3
        assert set(nodes) == {A, B, C}

    def test_no_duplicates_start_node_is_root_of_another(self):
        """
        Test that DFS does not visit the same node more than once when one startNode
        is the root of the whole graph, and also appears in the traversal path of
        another startNode in the list.

        Graph:
        A -> B -> C

        Starting DFS (reverse=False) from both C and A: visiting C will traverse
        C -> B -> A. A should not be discovered or finished a second time when it is
        encountered again as a startNode.
        """
        graph = Graph("")

        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)

        nodes, _ = graph.dfsOnFinish(startNodes=[C, A])

        # A must appear exactly once.
        assert len(nodes) == len(set(nodes)), "dfsOnFinish returned duplicate nodes"
        assert len(nodes) == 3
        assert set(nodes) == {A, B, C}

    def test_no_duplicates_reverse_start_node_is_descendant_of_another(self):
        """
        Test that reverse DFS does not visit the same node more than once when one
        startNode is a descendant (in the reverse traversal direction, i.e. toward
        leaves) of another startNode.

        Graph:
        A -> B -> C

        Starting reverse DFS from both A and B: visiting A first traverses A -> B -> C.
        B and C should not be discovered a second time when B is encountered again as
        a startNode.
        """
        graph = Graph("")

        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)

        nodes, _ = graph.dfsOnDiscover(startNodes=[A, B], reverse=True)

        # B must appear exactly once — it is visited when traversing forward from A,
        # and must NOT be re-visited when encountered as a startNode.
        assert len(nodes) == len(set(nodes)), "dfsOnDiscover(reverse=True) returned duplicate nodes"
        assert set(nodes) == {A, B, C}

    def test_no_duplicates_discover_start_node_is_ancestor_of_another(self):
        """
        Test that dfsOnDiscover does not return duplicate nodes when one startNode
        is an ancestor (in the traversal direction) of another startNode.

        Graph:
        A -> B -> C

        Starting dfsOnDiscover (reverse=False) from both C and B: visiting C first
        traverses C -> B -> A. B should not be discovered a second time when it is
        encountered again as a startNode.
        """
        graph = Graph("")

        A = graph.addNewNode("Ls", input="/tmp")
        B = graph.addNewNode("AppendText", inputText=A.output)
        C = graph.addNewNode("AppendText", inputText=B.output)

        nodes, _ = graph.dfsOnDiscover(startNodes=[C, B])

        assert len(nodes) == len(set(nodes)), "dfsOnDiscover returned duplicate nodes"
        assert set(nodes) == {A, B, C}
