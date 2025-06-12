from meshroom.core.graph import Graph
import math
import logging

logger = logging.getLogger('test')


def test_groupAttributes_with_same_structure_can_be_linked_and_only_calue_is_copied():
        
    # Given
    graph = Graph()
    position = graph.addNewNode("Position")
    color = graph.addNewNode("Color")
    
    # When
    graph.addEdge(position.xyz, color.rgb)
    position.xyz.x.value = 1.0
    position.xyz.y.value = 2.0
    position.xyz.z.value = 3.0

    # Then
    assert color.rgb.value != position.xyz.value
    assert math.isclose(color.rgb.r.value, position.xyz.x.value)
    assert math.isclose(color.rgb.g.value, position.xyz.y.value)
    assert math.isclose(color.rgb.b.value, position.xyz.z.value)
    assert math.isclose(color.rgb.r.value, 1.0)
    assert math.isclose(color.rgb.g.value, 2.0)
    assert math.isclose(color.rgb.b.value, 3.0)

def test_groupAttributes_with_same_nested_structure_can_be_linked_and_only_calue_is_copied():
        
    # Given
    graph = Graph()
    nestedColor = graph.addNewNode("NestedColor")
    nestedPosition = graph.addNewNode("NestedPosition")
    
    # When
    graph.addEdge(nestedPosition.xyz, nestedColor.rgb)
    nestedPosition.xyz.x.value = 1.0
    nestedPosition.xyz.y.value = 2.0
    nestedPosition.xyz.z.value = 3.0
    nestedPosition.xyz.test.x.value = 4.0
    nestedPosition.xyz.test.y.value = 5.0
    nestedPosition.xyz.test.z.value = 6.0

    # Then
    assert nestedColor.rgb.value != nestedPosition.xyz.test.value
    assert math.isclose(nestedColor.rgb.r.value, nestedPosition.xyz.x.value)
    assert math.isclose(nestedColor.rgb.g.value, nestedPosition.xyz.y.value)
    assert math.isclose(nestedColor.rgb.b.value, nestedPosition.xyz.z.value)
    assert math.isclose(nestedColor.rgb.test.r.value, nestedPosition.xyz.test.x.value)
    assert math.isclose(nestedColor.rgb.test.g.value, nestedPosition.xyz.test.y.value)
    assert math.isclose(nestedColor.rgb.test.b.value, nestedPosition.xyz.test.z.value)
    assert math.isclose(nestedColor.rgb.r.value, 1.0)
    assert math.isclose(nestedColor.rgb.g.value, 2.0)
    assert math.isclose(nestedColor.rgb.b.value, 3.0)
    assert math.isclose(nestedColor.rgb.test.r.value, 4.0)
    assert math.isclose(nestedColor.rgb.test.g.value, 5.0)
    assert math.isclose(nestedColor.rgb.test.b.value, 6.0)

def test_groupAttributes_with_smae_structure_should_allow_connection():

    # Given
    graph = Graph()
    nestedPosition = graph.addNewNode("NestedPosition")
    nestedColor = graph.addNewNode("NestedColor")
    
    # When
    acceptedConnection = nestedPosition.xyz.validateConnectionFrom(nestedColor.rgb)

    # Then
    assert acceptedConnection == True

def test_groupAttributes_with_different_structure_should_not_allow_connection():

    # Given
    graph = Graph()
    nestedPosition = graph.addNewNode("NestedPosition")
    nestedTest = graph.addNewNode("NestedTest")
    
    # When
    acceptedConnection = nestedPosition.xyz.validateConnectionFrom(nestedTest.xyz)

    # Then
    assert acceptedConnection == False