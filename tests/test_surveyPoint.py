import math

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.surveyPoint import (
    getNodeSurveyPointData,
    getNodeSurveyPointPositions,
    getSelectedSurveyPointObservationKey,
    getSurveyPointObservationKey,
    normalizeViewId,
    observationToSurveyPoint,
)

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithSurveyPoints(desc.Node):
    inputs = [
        desc.SurveyPoint(
            name="surveyPoint",
            label="Survey Point",
            description="A survey point.",
        ),
        desc.SurveyPoint(
            name="keyableSurveyPoint",
            label="Keyable Survey Point",
            description="A keyable survey point.",
            keyable=True,
            keyType="viewId"
        ),
        desc.ShapeList(
            name="surveyPointList",
            label="Survey Point List",
            description="Survey point list.",
            shape=desc.SurveyPoint(
                name="surveyPoint",
                label="Survey Point",
                description="A survey point.",
            ),
        ),
    ]


class NodeWithoutSurveyPoint(desc.Node):
    inputs = [
        desc.Point2d(
            name="point",
            label="Point 2d",
            description="A 2d point.",
        ),
    ]


def makeObservation(X=0.0, Y=0.0, Z=0.0, picked=False):
    return {"X": X, "Y": Y, "Z": Z, "x": 0.0, "y": 0.0, "ex": float("nan"), "ey": float("nan"), "picked": picked}


class TestSurveyPoint:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithSurveyPoints)
        registerNodeDesc(NodeWithoutSurveyPoint)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithSurveyPoints)
        unregisterNodeDesc(NodeWithoutSurveyPoint)

    def test_hasDisplayableSurveyPoint(self):
        graph = Graph("")
        assert graph.addNewNode(NodeWithSurveyPoints.__name__).hasDisplayableSurveyPoint
        assert not graph.addNewNode(NodeWithoutSurveyPoint.__name__).hasDisplayableSurveyPoint

    def test_normalizeViewId(self):
        assert normalizeViewId(None) is None
        assert normalizeViewId("") is None
        assert normalizeViewId(-1) is None
        assert normalizeViewId("-1") is None
        assert normalizeViewId(42) == "42"

    def test_observationKey(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)

        # Static survey point: single observation stored under key "0", whatever the view
        assert getSurveyPointObservationKey(node.surveyPoint, "42") == "0"
        # Keyable survey point: one observation per valid view id
        assert getSurveyPointObservationKey(node.keyableSurveyPoint, 42) == "42"
        assert getSurveyPointObservationKey(node.keyableSurveyPoint, "-1") is None
        # Not a survey point
        assert getSurveyPointObservationKey(None, "42") is None

    def test_observationToSurveyPoint(self):
        # Y and Z are flipped to convert to GL space
        assert observationToSurveyPoint({"X": 1.0, "Y": 2.0, "Z": 3.0}) == (1.0, -2.0, -3.0)
        assert observationToSurveyPoint(None) is None
        assert observationToSurveyPoint({"X": 1.0}) is None
        assert observationToSurveyPoint({"X": "a", "Y": 0.0, "Z": 0.0}) is None

    def test_nodeSurveyPointData(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)
        node.surveyPoint.geometry.setObservation("0", makeObservation(1.0, 2.0, 3.0, picked=True))
        node.keyableSurveyPoint.geometry.setObservation("7", makeObservation(4.0, 5.0, 6.0, picked=False))
        node.surveyPointList.append(None)
        node.surveyPointList.at(0).geometry.setObservation("0", makeObservation(7.0, 8.0, 9.0, picked=True))

        data = getNodeSurveyPointData(node, "7")
        assert [item["fullName"] for item in data] == [
            node.surveyPoint.fullName, node.keyableSurveyPoint.fullName, node.surveyPointList.at(0).fullName]
        assert [item["picked"] for item in data] == [True, False, True]

        # Only picked survey points have a position
        assert getNodeSurveyPointPositions(node, "7") == [(1.0, -2.0, -3.0), (7.0, -8.0, -9.0)]
        # Keyable survey point has no observation for this view
        assert len(getNodeSurveyPointData(node, "8")) == 2

    def test_selectedSurveyPointObservationKey(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)
        otherNode = graph.addNewNode(NodeWithSurveyPoints.__name__)

        assert getSelectedSurveyPointObservationKey(graph, node, node.surveyPoint.fullName, "3") == "0"
        assert getSelectedSurveyPointObservationKey(graph, node, node.keyableSurveyPoint.fullName, "3") == "3"
        # Shape must belong to the selected node
        assert getSelectedSurveyPointObservationKey(graph, otherNode, node.surveyPoint.fullName, "3") == ""
        assert getSelectedSurveyPointObservationKey(graph, node, "", "3") == ""
        assert getSelectedSurveyPointObservationKey(graph, None, node.surveyPoint.fullName, "3") == ""

    def test_keyableNanValueAsDict(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)
        node.keyableSurveyPoint.geometry.setObservation("1", makeObservation())

        assert math.isnan(node.keyableSurveyPoint.geometry.getObservation("1")["ex"])
        # NaN is not valid JSON: keyable values are exported as the 'nan' string
        valueDict = node.keyableSurveyPoint.geometry.getValueAsDict()
        assert valueDict["1"]["ex"] == "nan"
        assert valueDict["1"]["X"] == 0.0
