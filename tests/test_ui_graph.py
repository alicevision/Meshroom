#!/usr/bin/env python
# coding:utf-8

from meshroom.ui.graph import UIGraph


def test_duplicate_nodes():
    """
    Test nodes duplication.
    """

    # n0 -- n1 -- n2
    #   \          \
    #    ---------- n3

    g = UIGraph()
    n0 = g.addNewNode('Ls', input='/tmp')
    n1 = g.addNewNode('Ls', input=n0.output)
    n2 = g.addNewNode('Ls', input=n1.output)
    n3 = g.addNewNode('AppendFiles', input=n1.output, input2=n2.output)

    # duplicate from n1
    nMap = g.duplicateNodesFromNode(fromNode=n1)
    for s, d in nMap.items():
        assert s.nodeType == d.nodeType

    # check number of duplicated nodes
    assert len(nMap) == 3

    # check connections
    assert nMap[n1].input.getLinkParam() == n0.output
    assert nMap[n2].input.getLinkParam() == nMap[n1].output
    assert nMap[n3].input.getLinkParam() == nMap[n1].output
    assert nMap[n3].input2.getLinkParam() == nMap[n2].output
