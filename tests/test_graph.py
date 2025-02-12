from meshroom.core.graph import Graph, loadGraph
import os
import tempfile
import pytest

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
    #  /---/---->
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
    #  /---/---->
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
    flowEdgesRes = [
        (tB, tA),
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
    # Get all nodes from A (order not guaranteed)
    nodes = graph.dfsOnDiscover(startNodes=[A], reverse=True)[0]
    assert set(nodes) == {A, B, C, D, E, F}
    # Get all nodes from B
    nodes = graph.dfsOnDiscover(startNodes=[B], reverse=True)[0]
    assert set(nodes) == {B, C, D, E, F}
    # Get all nodes of type AppendText from B
    nodes = graph.dfsOnDiscover(startNodes=[B], filterTypes=['AppendText'], reverse=True)[0]
    assert set(nodes) == {B, C, D, F}
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
    # Get all nodes from A (order not guaranteed)
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
    # 'Random' creation order (as when loading a file)
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
    # check connections (access the single duplicate per node)
    assert nMap[n1][0].input.getLinkParam() == n0.output
    assert nMap[n2][0].input.getLinkParam() == nMap[n1][0].output
    assert nMap[n3][0].input.getLinkParam() == nMap[n1][0].output
    assert nMap[n3][0].input2.getLinkParam() == nMap[n2][0].output
def test_save_and_load(tmp_path):
    """
    Test saving a graph to a file and loading it back.
    Verifies that the graph's nodes and edge connections remain preserved.
    """
    tmp_file = tmp_path / "graph_test.mg"
    graph = Graph('SaveLoadTest')
    node1 = graph.addNewNode('Ls', input='/tmp')
    node2 = graph.addNewNode('AppendText', inputText='echo Test')
    graph.addEdge(node1.output, node2.input)
    graph.save(filepath=str(tmp_file), setupProjectFile=False, template=False)
    assert os.path.isfile(str(tmp_file))
    loaded_graph = loadGraph(str(tmp_file))
    assert len(loaded_graph.nodes.objects) == len(graph.nodes.objects)
    original_names = set(graph.nodes.objects.keys())
    loaded_names = set(loaded_graph.nodes.objects.keys())
    assert original_names == loaded_names
    original_edges = set((e.src.node.name, e.dst.getFullNameToNode()) for e in graph.edges)
    loaded_edges = set((e.src.node.name, e.dst.getFullNameToNode()) for e in loaded_graph.edges)
    assert original_edges == loaded_edges
def test_update_and_reset_links():
    """
    Test the static methods updateLinks and resetExternalLinks.
    We simulate attributes that include link expressions and verify that:
      - updateLinks replaces old node names with new ones in the attribute strings (and lists).
      - resetExternalLinks resets link expressions to default values if they do not reference allowed new node names.
    """
    attrs = {
        "a": "{oldNode.output}",
        "b": ["unrelated", "{oldNode.input}"],
        "c": "normal"  # should remain unchanged as it is not a link expression.
    }
    nameCorrespondences = {"oldNode": "newNode"}
    updated_attrs = Graph.updateLinks(attrs.copy(), nameCorrespondences)
    assert updated_attrs["a"] == "{newNode.output}"
    assert "unrelated" in updated_attrs["b"]
    found = False
    for v in updated_attrs["b"]:
        if isinstance(v, str) and "newNode" in v:
            assert v == "{newNode.input}"
            found = True
    assert found, "Expected link expression not found in list attribute"
    assert updated_attrs["c"] == "normal"
    updated_attrs["d"] = "{otherNode.param}"
    class DummyAttrDesc:
        def __init__(self, name, default):
            self.name = name
            self.value = default
    dummy_desc_list = [
        DummyAttrDesc("a", "defaultA"),
        DummyAttrDesc("b", "defaultB"),
        DummyAttrDesc("d", "defaultD")
    ]
    allowed_new_names = ["newNode"]
    reset_attrs = Graph.resetExternalLinks(updated_attrs.copy(), dummy_desc_list, allowed_new_names)
    assert reset_attrs["a"] == "{newNode.output}"
    assert reset_attrs["b"] == updated_attrs["b"]
    assert reset_attrs["d"] == "defaultD"
def test_edge_error_conditions():
    """
    Test error conditions in the Graph edge methods:
      1. Adding an edge connecting nodes from different graphs raises a RuntimeError.
      2. Removing a non-existent edge raises a RuntimeError.
    """
    graph1 = Graph("Graph1")
    nodeA = graph1.addNewNode('Ls', input='/tmp')
    graph2 = Graph("Graph2")
    nodeB = graph2.addNewNode('AppendText', inputText='echo from graph2')
    with pytest.raises(RuntimeError, match="The attributes of the edge should be part of a common graph."):
        graph1.addEdge(nodeA.output, nodeB.input)
    graph3 = Graph("Graph3")
    nodeC = graph3.addNewNode('Ls', input='/tmp')
    nodeD = graph3.addNewNode('AppendText', inputText='echo from graph3')
    edge = graph3.addEdge(nodeC.output, nodeD.input)
    graph3.removeEdge(nodeD.input)
    with pytest.raises(RuntimeError, match='is not connected'):
        graph3.removeEdge(nodeD.input)
def test_can_submit_or_compute_and_file_date():
    """
    Test canSubmitOrCompute for a new node and the getFileDateVersionFromPath utility.
    """
    g = Graph("TestCanSubmit")
    node = g.addNewNode("Ls", input="/tmp")
    assert g.canSubmitOrCompute(node) == 3
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
    try:
        mod_time = os.path.getmtime(tmp_name)
        retrieved_time = g.getFileDateVersionFromPath(tmp_name)
        assert abs(mod_time - retrieved_time) < 1.0
    finally:
        os.remove(tmp_name)
def test_clear_graph():
    """
    Test that calling clear() on a Graph instance resets its state:
      - Clears the header.
      - Removes all nodes and edges.
      - Unsets the internal filepath.
    """
    graph = Graph("TestClear")
    n1 = graph.addNewNode('Ls', input='/tmp')
    n2 = graph.addNewNode('AppendText', inputText='echo Test')
    graph.addEdge(n1.output, n2.input)
    graph.header["customKey"] = "customValue"
    graph._filepath = "dummy_project.mg"
    assert graph.header.get("customKey") == "customValue"
    assert len(graph.nodes.objects) > 0
    assert len(graph.edges.objects) > 0
    assert graph.filepath == "dummy_project.mg"
    graph.clear()
    assert graph.header == {}
    assert not graph.nodes.objects
    assert not graph.edges.objects
    assert graph.filepath == ""
def test_dfs_max_edge_length():
    """
    Test the dfsMaxEdgeLength method by constructing a simple chain graph:
        A -> B -> C
    and verifying that the computed scores for each edge match expectations.
    """
    graph = Graph("ChainGraph")
    A = graph.addNewNode("Ls", input="/tmp")
    B = graph.addNewNode("AppendText", inputText="echo B")
    C = graph.addNewNode("AppendText", inputText="echo C")
    graph.addEdge(A.output, B.input)
    graph.addEdge(B.output, C.input)
    scores = graph.dfsMaxEdgeLength()
    score_dict = {(u.name, v.name): score for (u, v), score in scores.items()}
    assert score_dict.get((B.name, A.name), 0) == 1
    assert score_dict.get((C.name, A.name), 0) == 2
    assert score_dict.get((C.name, B.name), 0) == 1
def test_update_nodes_and_attributes():
    """
    Test updateNodesPerUid and attribute retrieval methods.
    """
    graph = Graph("TestUpdateAndAttributes")
    node1 = graph.addNewNode("Ls", input="/tmp")
    node2 = graph.addNewNode("Ls", input="/var")
    common_uid = "12345-duplicate"
    node1._uid = common_uid
    node2._uid = common_uid
    graph.updateNodesPerUid()
    assert node1._uid == node2._uid == common_uid
    if hasattr(node1, "duplicates") and node1.duplicates is not None:
        all_dup_ids = [dup._uid for dup in node1.duplicates]
        assert common_uid in all_dup_ids
    if hasattr(node2, "duplicates") and node2.duplicates is not None:
        all_dup_ids = [dup._uid for dup in node2.duplicates]
        assert common_uid in all_dup_ids
    full_attr_name = "{}.input".format(node1.name)
    attr = graph.attribute(full_attr_name)
    assert attr is not None, "Expected to retrieve attribute '{}' from node '{}'".format(full_attr_name, node1.name)
    non_existent_attr = "{}.nonexistent".format(node1.name)
    int_attr = graph.internalAttribute(non_existent_attr)
    assert int_attr is None, "Non existent internal attribute '{}' should return None".format(non_existent_attr)
    graph_str = graph.asString()
    assert isinstance(graph_str, str)
    graph_dict = graph.toDict()
    assert node1.name in graph_dict
    assert node2.name in graph_dict
def test_load_legacy_format(tmp_path):
    """
    Test loading a legacy Meshroom graph file (fileVersion < 2.0) that uses the old UID format.
    This test verifies that the retro-compatibility code in _load properly updates the file content.
    """
    # Create a legacy-format graph file content with old uid formatting.
    legacy_content = '''{
        "header": {
            "fileVersion": "1.0",
            "NodesVersions": {"Ls": "0.0"}
        },
        "graph": {
            "node1": {
                "nodeType": "Ls",
                "uid": "{uid0}",
                "uids": {"0": "abc123"},
                "inputs": {"input": "/tmp"},
                "outputs": {}
            }
        }
    }'''
    file_path = tmp_path / "legacy.mg"
    file_path.write_text(legacy_content)
    # Load the legacy graph file.
    graph = loadGraph(str(file_path))
    
    # Verify that the graph has one node named "node1".
    assert "node1" in graph.nodes.objects
    node = graph.node("node1")
    assert node.nodeType == "Ls"
    
    # Verify that an input attribute is present and has the correct value.
    input_attr = node.attribute("input")
    assert input_attr is not None, "The input attribute should exist."
    assert input_attr.value == "/tmp"
    # Optionally, verify that the legacy uid has been updated (i.e. the "uids" field was processed).
    # Note: the actual UID computation is implemented in Node or nodeFactory – here we check that node._uid
    # is not the legacy placeholder "{uid0}".
    assert getattr(node, "_uid", None) != "{uid0}"