from meshroom.core import desc
from meshroom.core.graph import Graph

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

        # Check attribute number of observations
        # Should be 1 for static shape (default)
        assert node.point.nbObservations == 1
        assert node.line.nbObservations == 1
        assert node.rectangle.nbObservations == 1
        assert node.circle.nbObservations == 1
        # Should be 0 for keyable shape
        assert node.keyablePoint.nbObservations == 0
        assert node.keyableLine.nbObservations == 0
        assert node.keyableRectangle.nbObservations == 0
        assert node.keyableCircle.nbObservations == 0

        # Check attribute shape keyable
        # Should be false for static shape
        assert not node.point.shapeKeyable
        assert not node.line.shapeKeyable
        assert not node.rectangle.shapeKeyable
        assert not node.circle.shapeKeyable
        # Should be true for keyable shape
        assert node.keyablePoint.shapeKeyable
        assert node.keyableLine.shapeKeyable
        assert node.keyableRectangle.shapeKeyable
        assert node.keyableCircle.shapeKeyable


    def test_staticShape(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x" : 1, "y" : 1}
        observationLine = {"a" : {"x" : 1, "y" : 1}, "b" : {"x" : 2, "y" : 2}}
        observationRectangle = {"center" : {"x" : 10, "y" : 10}, "size" : {"width" : 20, "height" : 20}}
        observationCircle = {"center" : {"x" : 10, "y" : 10}, "radius" : 20}

        # Check attribute has observation, should be true (default)
        assert node.point.hasObservation("0")
        assert node.line.hasObservation("0")
        assert node.rectangle.hasObservation("0")
        assert node.circle.hasObservation("0")

        # Check attribute get observation, should be default value
        assert node.point.getObservation("0") == node.point.getDefaultValue()
        assert node.line.getObservation("0") == node.line.getDefaultValue()
        assert node.rectangle.getObservation("0") == node.rectangle.getDefaultValue()
        assert node.circle.getObservation("0") == node.circle.getDefaultValue()

        # Create observation at key "0"
        # Attribute are not keyable, key has no effect
        node.point.setObservation("0", observationPoint)
        node.line.setObservation("0", observationLine)
        node.rectangle.setObservation("0", observationRectangle)
        node.circle.setObservation("0", observationCircle)

        # Check attribute has observation, should be true
        assert node.point.hasObservation("0")
        assert node.line.hasObservation("0")
        assert node.rectangle.hasObservation("0")
        assert node.circle.hasObservation("0")

        # Check attribute get observation, should be created observation
        assert node.point.getObservation("0") == observationPoint
        assert node.line.getObservation("0") == observationLine
        assert node.rectangle.getObservation("0") == observationRectangle
        assert node.circle.getObservation("0") == observationCircle

        # Update attribute observation
        node.point.setObservation("0", {"x" : 2})
        node.line.setObservation("0", {"a" : {"x" : 2, "y": 2}})
        node.rectangle.setObservation("0", {"center" : {"x" : 20, "y" : 20}})
        node.circle.setObservation("0", {"radius" : 40})

        # Check attribute get observation, should be updated observation
        assert node.point.getObservation("0").get("x") == 2
        assert node.line.getObservation("0").get("a") == {"x" : 2, "y": 2}
        assert node.rectangle.getObservation("0").get("center") == {"x" : 20, "y" : 20}
        assert node.circle.getObservation("0").get("radius") == 40

        # Reset attribute value
        node.point.resetToDefaultValue()
        node.line.resetToDefaultValue()
        node.rectangle.resetToDefaultValue()
        node.circle.resetToDefaultValue()

        # Check attribute get observation, should be default value
        assert node.point.getObservation("0") == node.point.getDefaultValue()
        assert node.line.getObservation("0") == node.line.getDefaultValue()
        assert node.rectangle.getObservation("0") == node.rectangle.getDefaultValue()
        assert node.circle.getObservation("0") == node.circle.getDefaultValue()


    def test_keyableShape(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x" : 1, "y" : 1}
        observationLine = {"a" : {"x" : 1, "y" : 1}, "b" : {"x" : 2, "y" : 2}}
        observationRectangle = {"center" : {"x" : 10, "y" : 10}, "size" : {"width" : 20, "height" : 20}}
        observationCircle = {"center" : {"x" : 10, "y" : 10}, "radius" : 20}

        # Check attribute has observation at key "0", should be false
        assert not node.keyablePoint.hasObservation("0")
        assert not node.keyableLine.hasObservation("0")
        assert not node.keyableRectangle.hasObservation("0")
        assert not node.keyableCircle.hasObservation("0")

        # Check attribute get observation at key "0", should be None (no observation)
        assert node.keyablePoint.getObservation("0") == None
        assert node.keyableLine.getObservation("0") == None
        assert node.keyableRectangle.getObservation("0") == None
        assert node.keyableCircle.getObservation("0") == None

        # Create observation at key "0"
        node.keyablePoint.setObservation("0", observationPoint)
        node.keyableLine.setObservation("0", observationLine)
        node.keyableRectangle.setObservation("0", observationRectangle)
        node.keyableCircle.setObservation("0", observationCircle)

        # Check attribute number of observations, should be 1
        assert node.keyablePoint.nbObservations == 1
        assert node.keyableLine.nbObservations == 1
        assert node.keyableRectangle.nbObservations == 1
        assert node.keyableCircle.nbObservations == 1

        # Create observation at key "1"
        node.keyablePoint.setObservation("1", observationPoint)
        node.keyableLine.setObservation("1", observationLine)
        node.keyableRectangle.setObservation("1", observationRectangle)
        node.keyableCircle.setObservation("1", observationCircle)

        # Check attribute number of observations, should be 2
        assert node.keyablePoint.nbObservations == 2
        assert node.keyableLine.nbObservations == 2
        assert node.keyableRectangle.nbObservations == 2
        assert node.keyableCircle.nbObservations == 2

        # Check attribute has observation, should be true
        assert node.keyablePoint.hasObservation("0")
        assert node.keyablePoint.hasObservation("1")
        assert node.keyableLine.hasObservation("0")
        assert node.keyableLine.hasObservation("1")
        assert node.keyableRectangle.hasObservation("0")
        assert node.keyableRectangle.hasObservation("1")
        assert node.keyableCircle.hasObservation("0")
        assert node.keyableCircle.hasObservation("1")

        # Check attribute get observation at key "0", should be created observation
        assert node.keyablePoint.getObservation("0") == observationPoint
        assert node.keyableLine.getObservation("0") == observationLine
        assert node.keyableRectangle.getObservation("0") == observationRectangle
        assert node.keyableCircle.getObservation("0") == observationCircle

        # Update attribute observation at key "1"
        node.keyablePoint.setObservation("1", {"x" : 2})
        node.keyableLine.setObservation("1", {"a" : {"x" : 2, "y": 2}})
        node.keyableRectangle.setObservation("1", {"center" : {"x" : 20, "y" : 20}})
        node.keyableCircle.setObservation("1", {"radius" : 40})

        # Check attribute get observation at key "1", should be updated observation
        assert node.keyablePoint.getObservation("1").get("x") == 2
        assert node.keyableLine.getObservation("1").get("a") == {"x" : 2, "y": 2}
        assert node.keyableRectangle.getObservation("1").get("center") == {"x" : 20, "y" : 20}
        assert node.keyableCircle.getObservation("1").get("radius") == 40

        # Remove attribute observation at key "0"
        node.keyablePoint.removeObservation("0")
        node.keyableLine.removeObservation("0")
        node.keyableRectangle.removeObservation("0")
        node.keyableCircle.removeObservation("0")

        # Check attribute has observation at key "0", should be false
        assert not node.keyablePoint.hasObservation("0")
        assert not node.keyableLine.hasObservation("0")
        assert not node.keyableRectangle.hasObservation("0")
        assert not node.keyableCircle.hasObservation("0")

        # Reset attribute value
        node.keyablePoint.resetToDefaultValue()
        node.keyableLine.resetToDefaultValue()
        node.keyableRectangle.resetToDefaultValue()
        node.keyableCircle.resetToDefaultValue()

        # Check attribute has observation at key "1", should be false
        assert not node.keyablePoint.hasObservation("0")
        assert not node.keyableLine.hasObservation("0")
        assert not node.keyableRectangle.hasObservation("0")
        assert not node.keyableCircle.hasObservation("0")

        # Check attribute number of observations, should be 0
        assert node.keyablePoint.nbObservations == 0
        assert node.keyableLine.nbObservations == 0
        assert node.keyableRectangle.nbObservations == 0
        assert node.keyableCircle.nbObservations == 0

    def test_shapeList(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        pointValue = {"x" : 1, "y" : 1}
        keyablePointValue = {}

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
        assert node.pointList.at(1).getValueAsDict() == pointValue
        assert node.keyablePointList.at(1).getValueAsDict() == keyablePointValue

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


    def test_linkAttribute(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithShapeAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithShapeAttributes.__name__)

        pointValue = {"x" : 1, "y" : 1}

        # Add link:
        # nodeB.pointList is a link for nodeA.pointList
        graph.addEdge(nodeA.pointList, nodeB.pointList)
        # nodeB.point is a link for nodeA.point
        graph.addEdge(nodeA.point, nodeB.point)

        # Check link
        assert nodeB.pointList.isLink == True
        assert nodeB.pointList.inputLink == nodeA.pointList
        assert nodeB.point.isLink == True
        assert nodeB.point.inputLink == nodeA.point

        # Set observation for nodeA.point
        nodeA.point.setObservation("0", pointValue)
        # Add 3 shape to nodeA.pointList
        nodeA.pointList.append(pointValue)
        nodeA.pointList.append(pointValue)
        nodeA.pointList.append(pointValue)

        # Check nodeB.point
        assert nodeB.point.getObservation(0) == pointValue

        # Check nodeB.pointList
        assert len(nodeB.pointList) == 3
        assert nodeB.pointList.at(0).getValueAsDict() == pointValue
        assert nodeB.pointList.at(1).getValueAsDict() == pointValue
        assert nodeB.pointList.at(2).getValueAsDict() == pointValue

        # Update nodeA.point and nodeA.pointList[1]
        nodeA.point.setObservation("0", {"x" : 2})
        nodeA.pointList.at(1).setObservation("0", {"x" : 2})

        # Check nodeB second shape
        assert nodeB.point.getObservation("0").get("x") == 2
        assert nodeB.pointList.at(1).getObservation("0").get("x") == 2

        # Check serialized value
        assert nodeB.point.getSerializedValue() == nodeA.point.asLinkExpr()
        assert nodeB.pointList.getSerializedValue() == nodeA.pointList.asLinkExpr()


    def test_exportDict(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithShapeAttributes.__name__)

        observationPoint = {"x" : 1, "y" : 1}
        observationLine = {"a" : {"x" : 1, "y" : 1}, "b" : {"x" : 2, "y" : 2}}
        observationRectangle = {"center" : {"x" : 10, "y" : 10}, "size" : {"width" : 20, "height" : 20}}
        observationCircle = {"center" : {"x" : 10, "y" : 10}, "radius" : 20}
        keyablePointValue = {"x" : {"0" : observationPoint.get("x")}, "y" : {"0" : observationPoint.get("y")}}

        # Check uninitialized shape attribute
        # Shape list attribute should be empty list
        assert node.pointList.getValuesAsDicts() == []
        assert node.keyablePointList.getValuesAsDicts() == []
        assert node.pointList.getShapesAsDicts() == []
        assert node.keyablePointList.getShapesAsDicts() == []
        # Not keyable shape attribute should be default
        assert node.point.getValueAsDict() == {"x" : -1, "y" : -1}
        assert node.line.getValueAsDict() == {"a" : {"x" : -1, "y" : -1}, "b" : {"x" : -1, "y" : -1}}
        assert node.rectangle.getValueAsDict() == {"center" : {"x" : -1, "y" : -1}, "size" : {"width" : -1, "height" : -1}}
        assert node.circle.getValueAsDict() == {"center" : {"x" : -1, "y" : -1}, "radius" : -1}
        assert node.point.getShapeAsDict() == {"name" : node.point.rootName, 
                                               "type" : node.point.type, 
                                               "properties" : {"color" : node.point.shapeColor, "x" : -1, "y" : -1}}
        assert node.line.getShapeAsDict() == {"name" : node.line.rootName, 
                                              "type" : node.line.type, 
                                              "properties" : {"color" : node.line.shapeColor, "a" : {"x" : -1, "y" : -1}, "b" : {"x" : -1, "y" : -1}}}
        assert node.rectangle.getShapeAsDict() == {"name" : node.rectangle.rootName, 
                                                   "type" : node.rectangle.type, 
                                                   "properties" : {"color" : node.rectangle.shapeColor, "center" : {"x" : -1, "y" : -1}, "size" : {"width" : -1, "height" : -1}}}
        assert node.circle.getShapeAsDict() == {"name" : node.circle.rootName, 
                                                "type" : node.circle.type, 
                                                "properties" : {"color" : node.circle.shapeColor, "center" : {"x" : -1, "y" : -1}, "radius" : -1}}
        # Keyable shape attribute should be empty dict
        assert node.keyablePoint.getValueAsDict() == {}
        assert node.keyableLine.getValueAsDict() == {}
        assert node.keyableRectangle.getValueAsDict() == {}
        assert node.keyableCircle.getValueAsDict() == {}
        assert node.keyablePoint.getShapeAsDict() == {"name" : node.keyablePoint.rootName, 
                                                      "type" : node.keyablePoint.type, 
                                                      "properties" : {"color" : node.keyablePoint.shapeColor},
                                                      "observations" : {}}
        assert node.keyableLine.getShapeAsDict() == {"name" : node.keyableLine.rootName, 
                                                     "type" : node.keyableLine.type, 
                                                     "properties" : {"color" : node.keyableLine.shapeColor},
                                                     "observations" : {}}
        assert node.keyableRectangle.getShapeAsDict() == {"name" : node.keyableRectangle.rootName, 
                                                          "type" : node.keyableRectangle.type, 
                                                          "properties" : {"color" : node.keyableRectangle.shapeColor},
                                                          "observations" : {}}
        assert node.keyableCircle.getShapeAsDict() == {"name" : node.keyableCircle.rootName, 
                                                       "type" : node.keyableCircle.type, 
                                                       "properties" : {"color" : node.keyableCircle.shapeColor},
                                                       "observations" : {}}

        # Add one shape with an observation
        node.pointList.append(observationPoint)
        node.keyablePointList.append(keyablePointValue)

        # Add one observation 
        node.point.setObservation("0", observationPoint)
        node.keyablePoint.setObservation("0", observationPoint)
        node.line.setObservation("0", observationLine)
        node.keyableLine.setObservation("0", observationLine)
        node.rectangle.setObservation("0", observationRectangle)
        node.keyableRectangle.setObservation("0", observationRectangle)
        node.circle.setObservation("0", observationCircle)
        node.keyableCircle.setObservation("0", observationCircle)

        # Check shape attribute
        # Shape list attribute should be empty dict
        assert node.pointList.getValuesAsDicts() == [observationPoint]
        assert node.keyablePointList.getValuesAsDicts() == [{"0" : observationPoint}]
        assert node.pointList.getShapesAsDicts()[0].get("properties") == {"color" : node.keyablePoint.shapeColor} | observationPoint
        assert node.keyablePointList.getShapesAsDicts()[0].get("observations") == {"0" : observationPoint}
        # Not keyable shape attribute should be default
        assert node.point.getValueAsDict() == observationPoint
        assert node.line.getValueAsDict() == observationLine
        assert node.rectangle.getValueAsDict() == observationRectangle
        assert node.circle.getValueAsDict() == observationCircle
        assert node.point.getShapeAsDict().get("properties") ==  {"color" : node.point.shapeColor} | observationPoint
        assert node.line.getShapeAsDict().get("properties") == {"color" : node.line.shapeColor} | observationLine
        assert node.rectangle.getShapeAsDict().get("properties") == {"color" : node.rectangle.shapeColor} | observationRectangle
        assert node.circle.getShapeAsDict().get("properties") == {"color" : node.circle.shapeColor} | observationCircle
        # Keyable shape attribute should be empty dict
        assert node.keyablePoint.getValueAsDict() == {"0" : observationPoint}
        assert node.keyableLine.getValueAsDict() == {"0" : observationLine}
        assert node.keyableRectangle.getValueAsDict() == {"0" : observationRectangle}
        assert node.keyableCircle.getValueAsDict() == {"0" : observationCircle}
        assert node.keyablePoint.getShapeAsDict().get("observations") == {"0" : observationPoint}
        assert node.keyableLine.getShapeAsDict().get("observations") == {"0" : observationLine}
        assert node.keyableRectangle.getShapeAsDict().get("observations") == {"0" : observationRectangle}
        assert node.keyableCircle.getShapeAsDict().get("observations") == {"0" : observationCircle}