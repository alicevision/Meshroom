from meshroom.core import desc
from meshroom.core.graph import Graph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithKeyableAttributes(desc.Node):
    inputs = [
        desc.BoolParam(
            name="keyableBool",
            label="Keyable Bool",
            description="A keyable bool parameter.",
            value=True,
            keyable=True,
            keyType="viewId"
        ),
        desc.IntParam(
            name="keyableInt",
            label="Keyable Integer",
            description="A keyable integer parameter.",
            value=5,
            range=(0, 100, 2),
            keyable=True,
            keyType="viewId"
        ),
        desc.FloatParam(
            name="keyableFloat",
            label="Keyable Float",
            description="A keyable float parameter.",
            value=5.5,
            range=(0.0, 100.0, 2.2),
            keyable=True,
            keyType="viewId"
        ),
    ]

class TestKeyableAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithKeyableAttributes)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithKeyableAttributes)

    def test_initialization(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithKeyableAttributes.__name__)

        # Check attribute is keyable
        assert nodeA.keyableBool.keyable
        assert nodeA.keyableInt.keyable
        assert nodeA.keyableFloat.keyable

        # Check attribute key type
        assert nodeA.keyableBool.keyValues.keyType == "viewId"
        assert nodeA.keyableInt.keyValues.keyType == "viewId"
        assert nodeA.keyableFloat.keyValues.keyType == "viewId"

        # Check attribute pairs empty
        assert nodeA.keyableBool.isDefault
        assert nodeA.keyableInt.isDefault
        assert nodeA.keyableFloat.isDefault

        # Check attribute description value
        assert nodeA.keyableBool.desc.value == True
        assert nodeA.keyableInt.desc.value == 5
        assert nodeA.keyableFloat.desc.value == 5.5

        # Check attribute default value
        assert nodeA.keyableBool.getDefaultValue() == {}
        assert nodeA.keyableInt.getDefaultValue() == {}
        assert nodeA.keyableFloat.getDefaultValue() == {}

        # Check attribute serialized value
        assert nodeA.keyableBool.getSerializedValue() == {}
        assert nodeA.keyableInt.getSerializedValue() == {}
        assert nodeA.keyableFloat.getSerializedValue() == {}

        # Check attribute string value
        assert nodeA.keyableBool.getValueStr() == "{}"
        assert nodeA.keyableInt.getValueStr() == "{}"
        assert nodeA.keyableFloat.getValueStr() == "{}"


    def test_createReadUpdateDelete(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithKeyableAttributes.__name__)

        # Check attribute value at key "0", should be default value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("0") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("0") == 5
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("0") == 5.5

        # Check attribute has key "0", should be False (no key)
        assert nodeA.keyableBool.keyValues.hasKey("0") == False
        assert nodeA.keyableInt.keyValues.hasKey("0") == False
        assert nodeA.keyableFloat.keyValues.hasKey("0") == False

        # Add attribute (key, value) at key "0"
        nodeA.keyableBool.keyValues.add("0", False)
        nodeA.keyableInt.keyValues.add("0", 10)
        nodeA.keyableFloat.keyValues.add("0", 10.1)

        # Check attribute value at key "0", should be the new value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("0") == False
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("0") == 10
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("0") == 10.1

        # Check attribute has key "0", should be True (key exists)
        assert nodeA.keyableBool.keyValues.hasKey("0") == True
        assert nodeA.keyableInt.keyValues.hasKey("0") == True
        assert nodeA.keyableFloat.keyValues.hasKey("0") == True

        # Update attribute (key, value) at key "0"
        nodeA.keyableBool.keyValues.add("0", True)
        nodeA.keyableInt.keyValues.add("0", 20)
        nodeA.keyableFloat.keyValues.add("0", 20.2)

        # Check attribute value at key "0", should be the new updated value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("0") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("0") == 20
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("0") == 20.2

        # Check attribute has key "0", should be True (key exists)
        assert nodeA.keyableBool.keyValues.hasKey("0") == True
        assert nodeA.keyableInt.keyValues.hasKey("0") == True
        assert nodeA.keyableFloat.keyValues.hasKey("0") == True

        # Remove (key, value) at key "0"
        nodeA.keyableBool.keyValues.remove("0")
        nodeA.keyableInt.keyValues.remove("0")
        nodeA.keyableFloat.keyValues.remove("0")

        # Check attributes values at key "0", should be default value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("0") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("0") == 5
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("0") == 5.5

        # Check attribute has key "0", should be False (no key)
        assert nodeA.keyableBool.keyValues.hasKey("0") == False
        assert nodeA.keyableInt.keyValues.hasKey("0") == False
        assert nodeA.keyableFloat.keyValues.hasKey("0") == False


    def test_multipleKeys(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithKeyableAttributes.__name__)

        # Add attribute (key, value) at key "0"
        nodeA.keyableBool.keyValues.add("0", False)
        nodeA.keyableInt.keyValues.add("0", 1)
        nodeA.keyableFloat.keyValues.add("0", 1.1)

        # Add attribute (key, value) at key "1"
        nodeA.keyableBool.keyValues.add("1", False)
        nodeA.keyableInt.keyValues.add("1", 2)
        nodeA.keyableFloat.keyValues.add("1", 2.2)

        # Add attribute (key, value) at key "2"
        nodeA.keyableBool.keyValues.add("2", True)
        nodeA.keyableInt.keyValues.add("2", 3)
        nodeA.keyableFloat.keyValues.add("2", 3.3)

        # Check attribute has key "0", should be True (key exists)
        assert nodeA.keyableBool.keyValues.hasKey("0") == True
        assert nodeA.keyableInt.keyValues.hasKey("0") == True
        assert nodeA.keyableFloat.keyValues.hasKey("0") == True

        # Check attribute has key "1", should be True (key exists)
        assert nodeA.keyableBool.keyValues.hasKey("1") == True
        assert nodeA.keyableInt.keyValues.hasKey("1") == True
        assert nodeA.keyableFloat.keyValues.hasKey("1") == True

        # Check attribute has key "2", should be True (key exists)
        assert nodeA.keyableBool.keyValues.hasKey("2") == True
        assert nodeA.keyableInt.keyValues.hasKey("2") == True
        assert nodeA.keyableFloat.keyValues.hasKey("2") == True

        # Check attributes values at key "0", should be default value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("0") == False
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("0") == 1
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("0") == 1.1

        # Check attributes values at key "1", should be default value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("1") == False
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("1") == 2
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("1") == 2.2

        # Check attributes values at key "2", should be default value
        assert nodeA.keyableBool.keyValues.getValueAtKeyOrDefault("2") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("2") == 3
        assert nodeA.keyableFloat.keyValues.getValueAtKeyOrDefault("2") == 3.3

        # Remove (key, value) at key "1"
        nodeA.keyableBool.keyValues.remove("1")
        nodeA.keyableInt.keyValues.remove("1")
        nodeA.keyableFloat.keyValues.remove("1")

        # Check attribute has key "1", should be False (no key)
        assert nodeA.keyableBool.keyValues.hasKey("1") == False
        assert nodeA.keyableInt.keyValues.hasKey("1") == False
        assert nodeA.keyableFloat.keyValues.hasKey("1") == False


    def test_linkAttribute(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithKeyableAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithKeyableAttributes.__name__)

        # Add some keys for nodeA.keyableInt
        nodeA.keyableInt.keyValues.add("0", 0)
        nodeA.keyableInt.keyValues.add("1", 1)
        nodeA.keyableInt.keyValues.add("2", 2)

        # Add link:
        # nodeB.keyableInt is a link for nodeA.keyableInt
        nodeA.keyableInt.connectTo(nodeB.keyableInt)

        # Check link
        assert nodeB.keyableInt.isLink == True
        assert nodeB.keyableInt.keyValues == nodeA.keyableInt.keyValues

        # Check existing (key, value) in nodeA.keyableInt and nodeB.keyableInt
        assert nodeA.keyableInt.keyValues.hasKey("1") == True
        assert nodeB.keyableInt.keyValues.hasKey("1") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("1") == 1
        assert nodeB.keyableInt.keyValues.getValueAtKeyOrDefault("1") == 1

        # Add a key to nodeB.keyableInt
        nodeB.keyableInt.keyValues.add("3", 3)

        # Check new (key, value) in nodeA.keyableInt and nodeB.keyableInt
        assert nodeA.keyableInt.keyValues.hasKey("3") == True
        assert nodeB.keyableInt.keyValues.hasKey("3") == True
        assert nodeA.keyableInt.keyValues.getValueAtKeyOrDefault("3") == 3
        assert nodeB.keyableInt.keyValues.getValueAtKeyOrDefault("3") == 3

        # Check nodeB.keyableInt serialized values
        assert nodeB.keyableInt.getSerializedValue() == nodeA.keyableInt.asLinkExpr()


    def test_uid(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithKeyableAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithKeyableAttributes.__name__)

        # Add some keys for nodeA.keyableInt
        nodeA.keyableInt.keyValues.add("0", 0)
        nodeA.keyableInt.keyValues.add("1", 1)
        nodeA.keyableInt.keyValues.add("2", 2)

        # Add the same keys for nodeB.keyableInt
        # But not in the same order
        nodeB.keyableInt.keyValues.add("2", 2)
        nodeB.keyableInt.keyValues.add("0", 0)
        nodeB.keyableInt.keyValues.add("1", 1)

        # Check UID, should be the same
        assert nodeA.keyableInt.uid() == nodeB.keyableInt.uid()

        # Remove (key, value) at key "1" from nodeA.keyableInt
        nodeA.keyableInt.keyValues.remove("1")

        # Check UID, should not be the same
        assert nodeA.keyableInt.uid() != nodeB.keyableInt.uid()