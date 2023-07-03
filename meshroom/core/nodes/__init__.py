from typing import TYPE_CHECKING

def getNodeClass(nodeType: str):
    """
    Returns the appropriate subclass of `meshroom.core.node.Node` based on `nodeType`.

    Inputs
    ------
    nodeType: str
        the name of the node type
    
    Returns
    -------
    type[Node]
        the corresponding type class
    """
    if nodeType=="Meshing":
        from meshroom.core.nodes.MeshingNode import MeshingNode
        cls = MeshingNode
    else:
        from meshroom.core.node import Node
        cls = Node
    return cls