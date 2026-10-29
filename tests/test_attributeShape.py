from meshroom.core import desc
from meshroom.core.graph import Graph, loadGraph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithShapeAttributes(desc.Node):
    inputs = [
        desc.ShapeList(
            name="pointList",
            label="Point 2d List",
            description="Point 2d list.",
            shape=desc.Point2d(
                name="point",
                label="Point",
                description="A 2d point.",
            ),
        ),
        desc.ShapeList(
            name="keyablePointList",
            label="Keyable Point 2d List",
            description="Keyable point 2d list.",
            shape=desc.Point2d(
                name="point",
                label="Point",
                description="A 2d point.",
                keyable=True,
                keyType="viewId"
            ),
        ),
        desc.Point2d(
            name="point",
            label="Point 2d",
            description="A 2d point.",
        ),
        desc.Point2d(
            name="keyablePoint",
            label="Keyable Point 2d",
            description="A keyable 2d point.",
            keyable=True,
            keyType="viewId"
        ),
        desc.Line2d(
            name="line",
            label="Line 2d",
            description="A 2d line.",
        ),
        desc.Line2d(
            name="keyableLine",
            label="Keyable Line 2d",
            description="A keyable 2d line.",
            keyable=True,
            keyType="viewId"
        ),
        desc.Rectangle(
            name="rectangle",
            label="Rectangle",
            description="A rectangle.",
        ),
        desc.Rectangle(
            name="keyableRectangle",
            label="Keyable Rectangle",
            description="A keyable rectangle.",
            keyable=True,
            keyType="viewId"
        ),
        desc.Circle(
            name="circle",
            label="Circle",
            description="A circle.",
        ),
        desc.Circle(
            name="keyableCircle",
            label="Keyable Circle",
            description="A keyable circle.",
            keyable=True,
            keyType="viewId"
        ),
    ]


class TestShapeAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithShapeAttributes)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithShapeAttributes)

    def test_initialization(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        # ShapeListAttribute initialization

        # Check attribute has displayable shape (should be true)
        assert node.pointList.hasDisplayableShape
        assert node.keyablePointList.hasDisplayableShape

        # Check attribute type
        assert node.pointList.type == "ShapeList"
        assert node.keyablePointList.type == "ShapeList"

        # Check length
        # Should be 0, empty list
        assert len(node.pointList) == 0
        assert len(node.keyablePointList) == 0

        # ShapeAttribute initialization

        # Check attribute has displayable shape (should be true)
        assert node.point.hasDisplayableShape
        assert node.line.hasDisplayableShape
        assert node.rectangle.hasDisplayableShape
        assert node.circle.hasDisplayableShape
        assert node.keyablePoint.hasDisplayableShape
        assert node.keyableLine.hasDisplayableShape
        assert node.keyableRectangle.hasDisplayableShape
        assert node.keyableCircle.hasDisplayableShape

        # Check attribute type
        assert node.point.type == "Point2d"
        assert node.line.type == "Line2d"
        assert node.rectangle.type == "Rectangle"
        assert node.circle.type == "Circle"
        assert node.keyablePoint.type == "Point2d"
        assert node.keyableLine.type == "Line2d"
        assert node.keyableRectangle.type == "Rectangle"
        assert node.keyableCircle.type == "Circle"

        # Check attribute geometry number of observations
        # Should be 1 for static shape (default)
        assert node.point.geometry.nbObservations == 1
        assert node.line.geometry.nbObservations == 1
        assert node.rectangle.geometry.nbObservations == 1
        assert node.circle.geometry.nbObservations == 1
        # Should be 0 for keyable shape
        assert node.keyablePoint.geometry.nbObservations == 0
        assert node.keyableLine.geometry.nbObservations == 0
        assert node.keyableRectangle.geometry.nbObservations == 0
        assert node.keyableCircle.geometry.nbObservations == 0

        # Check shape attribute geometry observation keyable
        # Should be false for static shape
        assert not node.point.geometry.observationKeyable
        assert not node.line.geometry.observationKeyable
        assert not node.rectangle.geometry.observationKeyable
        assert not node.circle.geometry.observationKeyable
        # Should be true for keyable shape
        assert node.keyablePoint.geometry.observationKeyable
        assert node.keyableLine.geometry.observationKeyable
        assert node.keyableRectangle.geometry.observationKeyable
        assert node.keyableCircle.geometry.observationKeyable

    def test_staticShapeGeometry(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x": 1, "y": 1}
        observationLine = {"a": {"x": 1, "y": 1}, "b": {"x": 2, "y": 2}}
        observationRectangle = {"center": {"x": 10, "y": 10}, "size": {"width": 20, "height": 20}}
        observationCircle = {"center": {"x": 10, "y": 10}, "radius": 20}

        # Check static shape has observation, should be true (default)
        assert node.point.geometry.hasObservation("0")
        assert node.line.geometry.hasObservation("0")
        assert node.rectangle.geometry.hasObservation("0")
        assert node.circle.geometry.hasObservation("0")

        # Check static shape get observation, should be default value
        assert node.point.geometry.getObservation("0") == node.point.geometry.getDefaultValue()
        assert node.line.geometry.getObservation("0") == node.line.geometry.getDefaultValue()
        assert node.rectangle.geometry.getObservation("0") == node.rectangle.geometry.getDefaultValue()
        assert node.circle.geometry.getObservation("0") == node.circle.geometry.getDefaultValue()

        # Create observation at key "0"
        # For static shape key has no effect
        node.point.geometry.setObservation("0", observationPoint)
        node.line.geometry.setObservation("0", observationLine)
        node.rectangle.geometry.setObservation("0", observationRectangle)
        node.circle.geometry.setObservation("0", observationCircle)

        # Check static shape has observation, should be true
        assert node.point.geometry.hasObservation("0")
        assert node.line.geometry.hasObservation("0")
        assert node.rectangle.geometry.hasObservation("0")
        assert node.circle.geometry.hasObservation("0")

        # Check static shape get observation, should be created observation
        assert node.point.geometry.getObservation("0") == observationPoint
        assert node.line.geometry.getObservation("0") == observationLine
        assert node.rectangle.geometry.getObservation("0") == observationRectangle
        assert node.circle.geometry.getObservation("0") == observationCircle

        # Update static shape observation
        node.point.geometry.setObservation("0", {"x": 2})
        node.line.geometry.setObservation("0", {"a": {"x": 2, "y": 2}})
        node.rectangle.geometry.setObservation("0", {"center": {"x": 20, "y": 20}})
        node.circle.geometry.setObservation("0", {"radius": 40})

        # Check static shape get observation, should be updated observation
        assert node.point.geometry.getObservation("0").get("x") == 2
        assert node.line.geometry.getObservation("0").get("a") == {"x": 2, "y": 2}
        assert node.rectangle.geometry.getObservation("0").get("center") == {"x": 20, "y": 20}
        assert node.circle.geometry.getObservation("0").get("radius") == 40

        # Reset static shape geometry
        node.point.geometry.resetToDefaultValue()
        node.line.geometry.resetToDefaultValue()
        node.rectangle.geometry.resetToDefaultValue()
        node.circle.geometry.resetToDefaultValue()

        # Check static shape get observation, should be default value
        assert node.point.geometry.getObservation("0") == node.point.geometry.getDefaultValue()
        assert node.line.geometry.getObservation("0") == node.line.geometry.getDefaultValue()
        assert node.rectangle.geometry.getObservation("0") == node.rectangle.geometry.getDefaultValue()
        assert node.circle.geometry.getObservation("0") == node.circle.geometry.getDefaultValue()

    def test_keyableShapeGeometry(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x": 1, "y": 1}
        observationLine = {"a": {"x": 1, "y": 1}, "b": {"x": 2, "y": 2}}
        observationRectangle = {"center": {"x": 10, "y": 10}, "size": {"width": 20, "height": 20}}
        observationCircle = {"center": {"x": 10, "y": 10}, "radius": 20}

        # Check keyable shape has observation at key "0", should be false
        assert not node.keyablePoint.geometry.hasObservation("0")
        assert not node.keyableLine.geometry.hasObservation("0")
        assert not node.keyableRectangle.geometry.hasObservation("0")
        assert not node.keyableCircle.geometry.hasObservation("0")

        # Check keyable shape get observation at key "0", should be None (no observation)
        assert node.keyablePoint.geometry.getObservation("0") is None
        assert node.keyableLine.geometry.getObservation("0") is None
        assert node.keyableRectangle.geometry.getObservation("0") is None
        assert node.keyableCircle.geometry.getObservation("0") is None

        # Create observation at key "0"
        node.keyablePoint.geometry.setObservation("0", observationPoint)
        node.keyableLine.geometry.setObservation("0", observationLine)
        node.keyableRectangle.geometry.setObservation("0", observationRectangle)
        node.keyableCircle.geometry.setObservation("0", observationCircle)

        # Check keyable shape number of observations, should be 1
        assert node.keyablePoint.geometry.nbObservations == 1
        assert node.keyableLine.geometry.nbObservations == 1
        assert node.keyableRectangle.geometry.nbObservations == 1
        assert node.keyableCircle.geometry.nbObservations == 1

        # Create observation at key "1"
        node.keyablePoint.geometry.setObservation("1", observationPoint)
        node.keyableLine.geometry.setObservation("1", observationLine)
        node.keyableRectangle.geometry.setObservation("1", observationRectangle)
        node.keyableCircle.geometry.setObservation("1", observationCircle)

        # Check keyable shape number of observations, should be 2
        assert node.keyablePoint.geometry.nbObservations == 2
        assert node.keyableLine.geometry.nbObservations == 2
        assert node.keyableRectangle.geometry.nbObservations == 2
        assert node.keyableCircle.geometry.nbObservations == 2

        # Check keyable shape has observation, should be true
        assert node.keyablePoint.geometry.hasObservation("0")
        assert node.keyablePoint.geometry.hasObservation("1")
        assert node.keyableLine.geometry.hasObservation("0")
        assert node.keyableLine.geometry.hasObservation("1")
        assert node.keyableRectangle.geometry.hasObservation("0")
        assert node.keyableRectangle.geometry.hasObservation("1")
        assert node.keyableCircle.geometry.hasObservation("0")
        assert node.keyableCircle.geometry.hasObservation("1")

        # Check keyable shape get observation at key "0", should be created observation
        assert node.keyablePoint.geometry.getObservation("0") == observationPoint
        assert node.keyableLine.geometry.getObservation("0") == observationLine
        assert node.keyableRectangle.geometry.getObservation("0") == observationRectangle
        assert node.keyableCircle.geometry.getObservation("0") == observationCircle

        # Update keyable shape observation at key "1"
        node.keyablePoint.geometry.setObservation("1", {"x": 2})
        node.keyableLine.geometry.setObservation("1", {"a": {"x": 2, "y": 2}})
        node.keyableRectangle.geometry.setObservation("1", {"center": {"x": 20, "y": 20}})
        node.keyableCircle.geometry.setObservation("1", {"radius": 40})

        # Check keyable shape get observation at key "1", should be updated observation
        assert node.keyablePoint.geometry.getObservation("1").get("x") == 2
        assert node.keyableLine.geometry.getObservation("1").get("a") == {"x": 2, "y": 2}
        assert node.keyableRectangle.geometry.getObservation("1").get("center") == {"x": 20, "y": 20}
        assert node.keyableCircle.geometry.getObservation("1").get("radius") == 40

        # Remove keyable shape observation at key "0"
        node.keyablePoint.geometry.removeObservation("0")
        node.keyableLine.geometry.removeObservation("0")
        node.keyableRectangle.geometry.removeObservation("0")
        node.keyableCircle.geometry.removeObservation("0")

        # Check keyable shape has observation at key "0", should be false
        assert not node.keyablePoint.geometry.hasObservation("0")
        assert not node.keyableLine.geometry.hasObservation("0")
        assert not node.keyableRectangle.geometry.hasObservation("0")
        assert not node.keyableCircle.geometry.hasObservation("0")

        # Reset keyable shape geometry
        node.keyablePoint.geometry.resetToDefaultValue()
        node.keyableLine.geometry.resetToDefaultValue()
        node.keyableRectangle.geometry.resetToDefaultValue()
        node.keyableCircle.geometry.resetToDefaultValue()

        # Check keyable shape has observation at key "1", should be false
        assert not node.keyablePoint.geometry.hasObservation("0")
        assert not node.keyableLine.geometry.hasObservation("0")
        assert not node.keyableRectangle.geometry.hasObservation("0")
        assert not node.keyableCircle.geometry.hasObservation("0")

        # Check keyable shape number of observations, should be 0
        assert node.keyablePoint.geometry.nbObservations == 0
        assert node.keyableLine.geometry.nbObservations == 0
        assert node.keyableRectangle.geometry.nbObservations == 0
        assert node.keyableCircle.geometry.nbObservations == 0

    def test_shapeList(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        pointValue = {"userName": "testPoint", "userColor": "#fff", "geometry": {"x": 1, "y": 1}}
        keyablePointValue = {"userName": "testKeyablePoint", "userColor": "#fff", "geometry": {}}

        # Check visibility
        assert node.pointList.isVisible
        assert node.keyablePointList.isVisible

        # Check number of shapes, should be 0 (no shape)
        assert len(node.pointList) == 0
        assert len(node.keyablePointList) == 0

        # Add 3 elements
        node.pointList.append(pointValue)
        node.pointList.append(pointValue)
        node.pointList.append(pointValue)
        node.keyablePointList.append(keyablePointValue)
        node.keyablePointList.append(keyablePointValue)
        node.keyablePointList.append(keyablePointValue)

        # Check number of shapes, should be 3
        assert len(node.pointList) == 3
        assert len(node.keyablePointList) == 3

        # Check attribute second element
        assert node.pointList.at(1).geometry.getValueAsDict() == pointValue.get("geometry")
        assert node.keyablePointList.at(1).geometry.getValueAsDict() == keyablePointValue.get("geometry")

        # Change visibility
        node.pointList.isVisible = False
        node.keyablePointList.isVisible = False

        # Check shapes visibility
        assert not node.pointList.at(0).isVisible
        assert not node.pointList.at(1).isVisible
        assert not node.pointList.at(2).isVisible
        assert not node.keyablePointList.at(0).isVisible
        assert not node.keyablePointList.at(1).isVisible
        assert not node.keyablePointList.at(2).isVisible

        # Reset shape lists
        node.pointList.resetToDefaultValue()
        node.keyablePointList.resetToDefaultValue()

        # Check number of shapes, should be 0 (no shape)
        assert len(node.pointList) == 0
        assert len(node.keyablePointList) == 0

    def test_shapeListFullNameChangedOnShift(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)
        pointValue = {"userName": "testPoint", "userColor": "#fff", "geometry": {"x": 1, "y": 1}}
        for _ in range(3):
            node.pointList.append(pointValue)
        first, second, third = (node.pointList.at(i) for i in range(3))

        # Count fullNameChanged emissions for list elements and one of their children
        counts = {}
        for name, attribute in (("first", first), ("second", second), ("third", third),
                                ("thirdGeometry", third.geometry)):
            counts[name] = 0
            attribute.fullNameChanged.connect(lambda name=name: counts.__setitem__(name, counts[name] + 1))

        # Remove first element: the following elements (and their children) shift and are renamed
        node.pointList.remove(0)
        assert second.fullName.endswith("pointList[0]")
        assert third.fullName.endswith("pointList[1]")
        assert counts == {"first": 0, "second": 1, "third": 1, "thirdGeometry": 1}

        # Insert at the end: no element shifts
        node.pointList.append(pointValue)
        assert counts == {"first": 0, "second": 1, "third": 1, "thirdGeometry": 1}

        # Insert at the front: every existing element shifts
        node.pointList.insert(0, pointValue)
        assert counts == {"first": 0, "second": 2, "third": 2, "thirdGeometry": 2}

    def test_linkAttribute(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithShapeAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithShapeAttributes.__name__)

        pointGeometryValue = {"x": 1, "y": 1}
        pointValue = {"userName": "testPoint", "userColor": "#fff", "geometry": pointGeometryValue}

        # Add link:
        # nodeB.pointList is a link for nodeA.pointList
        nodeA.pointList.connectTo(nodeB.pointList)
        # nodeB.point is a link for nodeA.point
        nodeA.point.connectTo(nodeB.point)

        # Check link
        assert nodeB.pointList.isLink
        assert nodeB.pointList.inputLink == nodeA.pointList
        assert nodeB.point.isLink
        assert nodeB.point.inputLink == nodeA.point

        # Set observation for nodeA.point
        nodeA.point.geometry.setObservation("0", pointGeometryValue)
        # Add 3 shape to nodeA.pointList
        nodeA.pointList.append(pointValue)
        nodeA.pointList.append(pointValue)
        nodeA.pointList.append(pointValue)

        # Check nodeB.point geometry
        assert nodeB.point.geometry.getObservation(0) == pointGeometryValue

        # Check nodeB.pointList geometry
        assert len(nodeB.pointList) == 3
        assert nodeB.pointList.at(0).geometry.getValueAsDict() == pointGeometryValue
        assert nodeB.pointList.at(1).geometry.getValueAsDict() == pointGeometryValue
        assert nodeB.pointList.at(2).geometry.getValueAsDict() == pointGeometryValue

        # Update nodeA.point and nodeA.pointList[1] geometry
        nodeA.point.geometry.setObservation("0", {"x": 2})
        nodeA.pointList.at(1).geometry.setObservation("0", {"x": 2})

        # Check nodeB second shape geometry
        assert nodeB.point.geometry.getObservation("0").get("x") == 2
        assert nodeB.pointList.at(1).geometry.getObservation("0").get("x") == 2

        # Check serialized value
        assert nodeB.point.getSerializedValue() == nodeA.point.asLinkExpr()
        assert nodeB.pointList.getSerializedValue() == nodeA.pointList.asLinkExpr()

    def test_exportDict(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x": 1, "y": 1}
        observationLine = {"a": {"x": 1, "y": 1}, "b": {"x": 2, "y": 2}}
        observationRectangle = {"center": {"x": 10, "y": 10}, "size": {"width": 20, "height": 20}}
        observationCircle = {"center": {"x": 10, "y": 10}, "radius": 20}

        pointValue = {"userName": "testPoint", "userColor": "#fff", "geometry": observationPoint}
        keyablePointGeometryValue = {"x": {"0": observationPoint.get("x")}, "y": {"0": observationPoint.get("y")}}
        keyablePointValue = {"userName": "testKeyablePoint", "userColor": "#fff", "geometry": keyablePointGeometryValue}

        # Check uninitialized shape attribute
        # Shape list attribute should be empty list
        assert node.pointList.getGeometriesAsDict() == []
        assert node.keyablePointList.getGeometriesAsDict() == []
        assert node.pointList.getShapesAsDict() == []
        assert node.keyablePointList.getShapesAsDict() == []
        # Static shape attribute should be default
        assert node.point.geometry.getValueAsDict() == {"x": -1, "y": -1}
        assert node.line.geometry.getValueAsDict() == {"a": {"x": -1, "y": -1}, "b": {"x": -1, "y": -1}}
        assert node.rectangle.geometry.getValueAsDict() == {"center": {"x": -1, "y": -1}, "size": {"width": -1, "height": -1}}
        assert node.circle.geometry.getValueAsDict() == {"center": {"x": -1, "y": -1}, "radius": -1}
        assert node.point.getShapeAsDict() == {"name": node.point.rootName,
                                               "type": node.point.type,
                                               "properties": {"color": node.point.userColor, "x": -1, "y": -1}}
        assert node.line.getShapeAsDict() == {"name": node.line.rootName,
                                              "type": node.line.type,
                                              "properties": {"color": node.line.userColor, "a": {"x": -1, "y": -1}, "b": {"x": -1, "y": -1}}}
        assert node.rectangle.getShapeAsDict() == {"name": node.rectangle.rootName,
                                                   "type": node.rectangle.type,
                                                   "properties": {"color": node.rectangle.userColor, "center": {"x": -1, "y": -1}, "size": {"width": -1, "height": -1}}}
        assert node.circle.getShapeAsDict() == {"name": node.circle.rootName,
                                                "type": node.circle.type,
                                                "properties": {"color": node.circle.userColor, "center": {"x": -1, "y": -1}, "radius": -1}}
        # Keyable shape attribute should be empty dict
        assert node.keyablePoint.geometry.getValueAsDict() == {}
        assert node.keyableLine.geometry.getValueAsDict() == {}
        assert node.keyableRectangle.geometry.getValueAsDict() == {}
        assert node.keyableCircle.geometry.getValueAsDict() == {}
        assert node.keyablePoint.getShapeAsDict() == {"name": node.keyablePoint.rootName,
                                                      "type": node.keyablePoint.type,
                                                      "properties": {"color": node.keyablePoint.userColor},
                                                      "observations": {}}
        assert node.keyableLine.getShapeAsDict() == {"name": node.keyableLine.rootName,
                                                     "type": node.keyableLine.type,
                                                     "properties": {"color": node.keyableLine.userColor},
                                                     "observations": {}}
        assert node.keyableRectangle.getShapeAsDict() == {"name": node.keyableRectangle.rootName,
                                                          "type": node.keyableRectangle.type,
                                                          "properties": {"color": node.keyableRectangle.userColor},
                                                          "observations": {}}
        assert node.keyableCircle.getShapeAsDict() == {"name": node.keyableCircle.rootName,
                                                       "type": node.keyableCircle.type,
                                                       "properties": {"color": node.keyableCircle.userColor},
                                                       "observations": {}}

        # Add one shape with an observation
        node.pointList.append(pointValue)
        node.keyablePointList.append(keyablePointValue)

        # Add one observation
        node.point.geometry.setObservation("0", observationPoint)
        node.keyablePoint.geometry.setObservation("0", observationPoint)
        node.line.geometry.setObservation("0", observationLine)
        node.keyableLine.geometry.setObservation("0", observationLine)
        node.rectangle.geometry.setObservation("0", observationRectangle)
        node.keyableRectangle.geometry.setObservation("0", observationRectangle)
        node.circle.geometry.setObservation("0", observationCircle)
        node.keyableCircle.geometry.setObservation("0", observationCircle)

        # Check shape attribute
        # Shape list attribute should be empty dict
        assert node.pointList.getGeometriesAsDict() == [observationPoint]
        assert node.keyablePointList.getGeometriesAsDict() == [{"0": observationPoint}]
        assert node.pointList.getShapesAsDict()[0].get("properties") == {"color": pointValue.get("userColor")} | observationPoint
        assert node.keyablePointList.getShapesAsDict()[0].get("observations") == {"0": observationPoint}
        # Not keyable shape attribute should be default
        assert node.point.geometry.getValueAsDict() == observationPoint
        assert node.line.geometry.getValueAsDict() == observationLine
        assert node.rectangle.geometry.getValueAsDict() == observationRectangle
        assert node.circle.geometry.getValueAsDict() == observationCircle
        assert node.point.getShapeAsDict().get("properties") == {"color": node.point.userColor} | observationPoint
        assert node.line.getShapeAsDict().get("properties") == {"color": node.line.userColor} | observationLine
        assert node.rectangle.getShapeAsDict().get("properties") == {"color": node.rectangle.userColor} | observationRectangle
        assert node.circle.getShapeAsDict().get("properties") == {"color": node.circle.userColor} | observationCircle
        # Keyable shape attribute should be empty dict
        assert node.keyablePoint.geometry.getValueAsDict() == {"0": observationPoint}
        assert node.keyableLine.geometry.getValueAsDict() == {"0": observationLine}
        assert node.keyableRectangle.geometry.getValueAsDict() == {"0": observationRectangle}
        assert node.keyableCircle.geometry.getValueAsDict() == {"0": observationCircle}
        assert node.keyablePoint.getShapeAsDict().get("observations") == {"0": observationPoint}
        assert node.keyableLine.getShapeAsDict().get("observations") == {"0": observationLine}
        assert node.keyableRectangle.getShapeAsDict().get("observations") == {"0": observationRectangle}
        assert node.keyableCircle.getShapeAsDict().get("observations") == {"0": observationCircle}


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
    ]


class TestSurveyPointAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithSurveyPoints)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithSurveyPoints)

    def test_picked2dFlag(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)

        # Both the 3d and 2d parts are unset by default
        observation = node.surveyPoint.geometry.getObservation("0")
        assert observation["picked"] is False
        assert observation["picked2d"] is False
        assert node.keyableSurveyPoint.geometry.getObservation("0") is None

    def test_keyablePartialAndFullObservations(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)
        geometry = node.keyableSurveyPoint.geometry

        # A partial observation (3d part only) is not a complete observation
        geometry.setObservation("1", {"X": 1.0, "Y": 2.0, "Z": 3.0, "picked": True})
        assert not geometry.hasObservation("1")
        assert geometry.getObservation("1") is None

        # A full observation round-trips
        observation = {"X": 1.0, "Y": 2.0, "Z": 3.0, "x": -1.0, "y": -1.0, "ex": 0.0, "ey": 0.0,
                       "picked": True, "picked2d": False}
        geometry.setObservation("2", observation)
        assert geometry.hasObservation("2")
        assert geometry.getObservation("2") == observation

    def test_incompleteObservationIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)

        # Only the 3d part is set, the 2d part keeps its default values
        observation = {"X": 1.0, "Y": 2.0, "Z": 3.0, "x": -1.0, "y": -1.0, "ex": 0.0, "ey": 0.0,
                       "picked": True, "picked2d": False}
        node.keyableSurveyPoint.geometry.setObservation("1", observation)
        node.surveyPoint.geometry.setObservation("0", observation)
        graph.save()

        loadedNode = loadGraph(graph.filepath).node(node.name)
        assert loadedNode.keyableSurveyPoint.geometry.getObservation("1") == observation
        assert loadedNode.surveyPoint.geometry.getObservation("0") == observation

    def test_mergeKeepsOtherPart(self):
        from meshroom.ui.components.shapes.surveyPoint import mergeSurveyPointObservation

        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)

        for shape, key in ((node.keyableSurveyPoint, "1"), (node.surveyPoint, "0")):
            geometry = shape.geometry
            point3d = {"X": 1.0, "Y": 2.0, "Z": 3.0, "picked": True}

            # 3d pick first: full observation, the 2d part keeps its default values
            geometry.setObservation(key, mergeSurveyPointObservation(shape, key, point3d))
            assert geometry.hasObservation(key)
            assert geometry.getObservation(key)["picked2d"] is False

            # 2d placement keeps the 3d part
            geometry.setObservation(key, mergeSurveyPointObservation(shape, key, {"x": 10.0, "y": 20.0, "picked2d": True}))
            observation = geometry.getObservation(key)
            assert point3d.items() <= observation.items()
            assert (observation["x"], observation["y"], observation["picked2d"]) == (10.0, 20.0, True)

            # Removing the 2d part keeps the 3d part and the 2d position
            geometry.setObservation(key, mergeSurveyPointObservation(shape, key, {"picked2d": False}))
            observation = geometry.getObservation(key)
            assert point3d.items() <= observation.items()
            assert (observation["x"], observation["y"], observation["picked2d"]) == (10.0, 20.0, False)

    def test_upgradeWithoutPicked2d(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithSurveyPoints.__name__)

        # Values saved before the picked2d flag existed: placed in 2d if the 2d position is set
        node.surveyPoint.upgradeValue({"geometry": {"X": 1.0, "Y": 2.0, "Z": 3.0, "x": 10.0, "y": 20.0, "picked": True}})
        assert node.surveyPoint.geometry.getObservation("0")["picked2d"] is True

        node.keyableSurveyPoint.upgradeValue({"geometry": {
            "X": {"1": 1.0, "2": 1.0}, "Y": {"1": 2.0, "2": 2.0}, "Z": {"1": 3.0, "2": 3.0},
            "x": {"1": 10.0, "2": -1.0}, "y": {"1": 20.0, "2": -1.0},
            "ex": {"1": 0.0, "2": 0.0}, "ey": {"1": 0.0, "2": 0.0},
            "picked": {"1": True, "2": True}}})
        assert node.keyableSurveyPoint.geometry.getObservation("1")["picked2d"] is True
        assert node.keyableSurveyPoint.geometry.getObservation("2")["picked2d"] is False
