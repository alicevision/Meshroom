"""
Tests for the optional "automatic value" of IntParam/FloatParam descriptors:
a special value outside the range, stored as the attribute's regular value.
"""
from meshroom.core import desc
from meshroom.core.desc.attribute import ValueTypeErrors
from meshroom.core.graph import Graph
from meshroom.core.plugins.base import NodeDescProvider

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithAutoValue(desc.Node):
    inputs = [
        desc.IntParam(name="threads", value=0, range=(1, 64, 1), autoValue=0, autoLabel="Auto"),
        desc.FloatParam(name="limit", value=0.5, range=(0.0, 1.0, 0.1), autoValue=-1.0, autoLabel="No limit"),
    ]
    outputs = []

    def process(self, node):
        pass


class NodeWithInvalidAutoValue(desc.Node):
    inputs = [
        desc.IntParam(name="threads", value=2, range=(1, 64, 1), autoValue=8),
    ]
    outputs = []

    def process(self, node):
        pass


def test_defaultHasNoAutoValue():
    for param in (desc.IntParam(name="a", value=1, range=(1, 10, 1)),
                  desc.FloatParam(name="f", value=0.5, range=(0.0, 1.0, 0.1))):
        assert param.hasAutoValue is False
        assert param.autoValue is None
        assert param.autoLabel == "Auto"
        assert param.autoIcon == "motion_photos_auto"


def test_intAutoValue():
    param = desc.IntParam(name="a", value=0, range=(1, 10, 1), autoValue=0, autoLabel="No limit")
    assert param.hasAutoValue is True
    assert param.autoValue == 0
    assert param.autoLabel == "No limit"
    assert param.checkValueTypes() == ("", ValueTypeErrors.NONE)


def test_customAutoIcon():
    param = desc.IntParam(name="a", value=0, range=(1, 10, 1), autoValue=0, autoLabel="No limit", autoIcon="all_inclusive")
    assert param.autoIcon == "all_inclusive"
    assert param.clone().autoIcon == "all_inclusive"


def test_floatAutoValue():
    param = desc.FloatParam(name="f", value=-1.0, range=(0.0, 1.0, 0.1), autoValue=-1.0)
    assert param.hasAutoValue is True
    assert param.checkValueTypes() == ("", ValueTypeErrors.NONE)


def test_autoValueInsideRange():
    for autoValue in (0, 5, 10):
        param = desc.IntParam(name="a", value=1, range=(0, 10, 1), autoValue=autoValue)
        assert param.checkValueTypes() == ("a", ValueTypeErrors.AUTO_VALUE)
    param = desc.FloatParam(name="f", value=0.5, range=(0.0, 1.0, 0.1), autoValue=0.5)
    assert param.checkValueTypes() == ("f", ValueTypeErrors.AUTO_VALUE)


def test_autoValueWrongType():
    assert desc.IntParam(name="a", value=1, autoValue=0.5).checkValueTypes() == ("a", ValueTypeErrors.AUTO_VALUE)
    assert desc.IntParam(name="a", value=1, autoValue=True).checkValueTypes() == ("a", ValueTypeErrors.AUTO_VALUE)
    assert desc.FloatParam(name="f", value=1.0, autoValue=0).checkValueTypes() == ("f", ValueTypeErrors.AUTO_VALUE)


def test_autoValueNoRange():
    param = desc.IntParam(name="a", value=1, autoValue=-1)
    assert param.checkValueTypes() == ("", ValueTypeErrors.NONE)


def test_cloneKeepsRangeAndAutoValue():
    for param in (desc.IntParam(name="a", value=0, range=(1, 10, 1), autoValue=0, autoLabel="All"),
                  desc.FloatParam(name="f", value=0.5, range=(0.0, 1.0, 0.1), autoValue=-1.0, autoLabel="None")):
        cloned = param.clone()
        assert cloned.range == param.range
        assert cloned.autoValue == param.autoValue
        assert cloned.autoLabel == param.autoLabel


def test_invalidAutoValueReportedByProvider():
    provider = NodeDescProvider(NodeWithInvalidAutoValue)
    assert provider.error is not None
    assert "'autoValue'" in provider.error
    assert "threads" in provider.error


class TestAutoValueAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAutoValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAutoValue)

    def test_autoValueIsStoredValue(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithAutoValue.__name__)
        assert NodeDescProvider(NodeWithAutoValue).error is None
        assert node.threads.value == node.threads.desc.autoValue
        node.limit.value = -1.0
        assert node.limit.value == node.limit.desc.autoValue
        node.threads.value = 8
        assert node.threads.value == 8
        assert node.threads.value != node.threads.desc.autoValue


def test_autoValueValidatedWithoutDefaultValue():
    param = desc.IntParam(name="a", value=None, range=(1, 10, 1), autoValue=5)
    assert param.checkValueTypes() == ("a", ValueTypeErrors.AUTO_VALUE)
    param = desc.FloatParam(name="f", value=None, range=(0.0, 1.0, 0.1), autoValue=0.5)
    assert param.checkValueTypes() == ("f", ValueTypeErrors.AUTO_VALUE)
