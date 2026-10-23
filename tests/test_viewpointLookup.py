from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.ui.viewpointLookup import ViewpointLookup

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithViewpoints(desc.Node):
    inputs = [
        desc.ListAttribute(
            name="viewpoints",
            label="Viewpoints",
            description="",
            elementDesc=desc.GroupAttribute(
                name="viewpoint",
                label="Viewpoint",
                description="",
                items=[
                    desc.IntParam(name="viewId", label="Id", description="", value=-1, range=None),
                    desc.StringParam(name="path", label="Path", description="", value=""),
                ],
            ),
        ),
        desc.IntParam(name="intInput", label="Int Input", description="", value=0, range=None),
    ]


def referenceSearch(viewpoints, viewId):
    """ The linear search the lookup must be equivalent to. """
    return next((vp for vp in viewpoints if str(vp.viewId.value) == viewId), None)


def checkEquivalence(lookup, viewpoints):
    queries = {str(vp.viewId.value) for vp in viewpoints}
    queries |= {"-1", "0", "999", "0123", " 1", "+1", "1.0", "abc", "", "None"}
    for viewId in queries:
        assert lookup.get(viewpoints, viewId) is referenceSearch(viewpoints, viewId), viewId


def views(*viewIds):
    return [{"viewId": viewId, "path": f"/img_{viewId}.jpg"} for viewId in viewIds]


class TestViewpointLookup:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithViewpoints)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithViewpoints)

    def test_hitAndMiss(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(10, 20, 30))
        lookup = ViewpointLookup()
        viewpoints = node.viewpoints.value

        assert lookup.get(viewpoints, "20") is node.viewpoints.at(1)
        assert lookup.get(viewpoints, "40") is None
        assert lookup.get(None, "20") is None
        checkEquivalence(lookup, viewpoints)

    def test_duplicatesReturnFirstMatch(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(1, 2, 1, 2))
        lookup = ViewpointLookup()
        viewpoints = node.viewpoints.value

        assert lookup.get(viewpoints, "1") is node.viewpoints.at(0)
        assert lookup.get(viewpoints, "2") is node.viewpoints.at(1)
        checkEquivalence(lookup, viewpoints)

    def test_listModifiedInPlace(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(1, 2, 3))
        lookup = ViewpointLookup()
        viewpoints = node.viewpoints.value
        checkEquivalence(lookup, viewpoints)

        node.viewpoints.extend(views(4, 1))
        checkEquivalence(lookup, viewpoints)

        node.viewpoints.insert(0, views(3))
        assert lookup.get(viewpoints, "3") is node.viewpoints.at(0)
        checkEquivalence(lookup, viewpoints)

        node.viewpoints.remove(0, 2)
        checkEquivalence(lookup, viewpoints)

        # Same size, different viewpoints objects
        node.viewpoints.value = views(7, 8, 9, 10)
        checkEquivalence(lookup, viewpoints)

        node.viewpoints.value = []
        checkEquivalence(lookup, viewpoints)
        assert lookup.get(viewpoints, "7") is None

    def test_viewIdEdited(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(1, 2, 3))
        invalidations = []
        lookup = ViewpointLookup(onInvalidated=lambda: invalidations.append(True))
        viewpoints = node.viewpoints.value
        checkEquivalence(lookup, viewpoints)

        # A previous miss becomes a hit
        node.viewpoints.at(1).viewId.value = 5
        assert invalidations
        assert lookup.get(viewpoints, "5") is node.viewpoints.at(1)
        assert lookup.get(viewpoints, "2") is None
        checkEquivalence(lookup, viewpoints)

        # An earlier viewpoint now takes precedence on a later one
        node.viewpoints.at(0).viewId.value = 3
        assert lookup.get(viewpoints, "3") is node.viewpoints.at(0)
        checkEquivalence(lookup, viewpoints)

        node.viewpoints.at(2).viewId.resetToDefaultValue()
        checkEquivalence(lookup, viewpoints)

    def test_linkedViewId(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(1, 2))
        source = graph.addNewNode(NodeWithViewpoints.__name__, intInput=1)
        lookup = ViewpointLookup()
        viewpoints = node.viewpoints.value
        checkEquivalence(lookup, viewpoints)

        graph.addEdge(source.intInput, node.viewpoints.at(1).viewId)
        checkEquivalence(lookup, viewpoints)

        # Upstream changes are not notified on the linked viewId: must still be found
        source.intInput.value = 2
        assert lookup.get(viewpoints, "2") is node.viewpoints.at(1)
        checkEquivalence(lookup, viewpoints)

        graph.removeEdge(node.viewpoints.at(1).viewId)
        checkEquivalence(lookup, viewpoints)

    def test_severalLists(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(1, 2))
        nodeB = graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(2, 3))
        lookup = ViewpointLookup()

        for _ in range(2):
            assert lookup.get(nodeA.viewpoints.value, "2") is nodeA.viewpoints.at(1)
            assert lookup.get(nodeB.viewpoints.value, "2") is nodeB.viewpoints.at(0)
            assert lookup.get(nodeB.viewpoints.value, "1") is None

        # The attribute value is replaced by a new list: the old one is still searchable
        oldViewpoints = nodeA.viewpoints.value
        nodeA.viewpoints.resetToDefaultValue()
        assert nodeA.viewpoints.value is not oldViewpoints
        checkEquivalence(lookup, oldViewpoints)
        checkEquivalence(lookup, nodeA.viewpoints.value)

        # More lists than the cache can hold
        nodes = [graph.addNewNode(NodeWithViewpoints.__name__, viewpoints=views(i, i + 1))
                 for i in range(ViewpointLookup.MAX_LISTS + 2)]
        for _ in range(2):
            for n in nodes:
                checkEquivalence(lookup, n.viewpoints.value)
