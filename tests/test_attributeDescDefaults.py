"""
Tests for optional label/description/value arguments on attribute descriptors.

Covers:
- All param types can be created with minimal arguments (name only)
- Param descriptors created without a value are marked as dynamic (isDynamicValue=True)
- Output attributes with isDynamicValue=True have None as their runtime value
- Input attributes without a value return the expected type default at runtime
"""
import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph

from .utils import registerNodeDesc, unregisterNodeDesc


# ---------------------------------------------------------------------------
# A node whose inputs all use the descriptor default (value=None).
# Each typed param will have its type's zero-value as the runtime default.
# ---------------------------------------------------------------------------
class NodeWithMinimalInputs(desc.Node):
    inputs = [
        desc.File(name="fileInput"),
        desc.BoolParam(name="boolInput"),
        desc.IntParam(name="intInput"),
        desc.FloatParam(name="floatInput"),
        desc.StringParam(name="stringInput"),
        desc.ColorParam(name="colorInput"),
        desc.ChoiceParam(name="choiceInput", values=["a", "b", "c"]),
    ]
    outputs = []

    def process(self, node):
        pass


# ---------------------------------------------------------------------------
# A node whose outputs all use the descriptor default (value=None) so they
# are treated as dynamic values computed at runtime.
# ---------------------------------------------------------------------------
class NodeWithDynamicOutputsMinimal(desc.Node):
    inputs = []
    outputs = [
        desc.File(name="fileOutput"),
        desc.BoolParam(name="boolOutput"),
        desc.IntParam(name="intOutput"),
        desc.FloatParam(name="floatOutput"),
        desc.StringParam(name="stringOutput"),
    ]

    def process(self, node):
        pass


# ---------------------------------------------------------------------------
# Tests on the descriptor objects themselves (no Graph required)
# ---------------------------------------------------------------------------

# Pairs of (descriptor, expected_label_from_name)
_MINIMAL_DESCS = [
    desc.File(name="outputFile"),
    desc.BoolParam(name="myBool"),
    desc.IntParam(name="intValue"),
    desc.FloatParam(name="floatValue"),
    desc.StringParam(name="stringParam"),
    desc.ColorParam(name="primaryColor"),
    desc.PushButtonParam(name="applyButton"),
    desc.ChoiceParam(name="modeChoice"),
    desc.ListAttribute(desc.StringParam(name="elem"), name="itemList"),
    desc.GroupAttribute([], name="optionGroup"),
]


@pytest.mark.parametrize("attrDesc", _MINIMAL_DESCS, ids=lambda d: type(d).__name__)
def test_param_minimal_creation(attrDesc):
    """All attribute types should be constructible with minimal arguments (name only)."""
    assert attrDesc.name is not None
    assert attrDesc.label != ""       # label is auto-generated from the name
    assert attrDesc.description == "" # description defaults to empty string


@pytest.mark.parametrize("attrDesc", [
    desc.File(name="fileParam"),
    desc.BoolParam(name="boolParam"),
    desc.IntParam(name="intParam"),
    desc.FloatParam(name="floatParam"),
    desc.StringParam(name="stringParam"),
    desc.ColorParam(name="colorParam"),
    desc.PushButtonParam(name="pushButton"),
    desc.ChoiceParam(name="choiceParam"),
], ids=lambda d: type(d).__name__)
def test_param_no_value_is_dynamic(attrDesc):
    """Param descriptors created without a value should be marked as dynamic."""
    assert attrDesc.isDynamicValue is True


def test_label_auto_generated_from_camel_case():
    """Label should be auto-generated from camelCase attribute names."""
    assert desc.File(name="outputFile").label == "Output File"
    assert desc.IntParam(name="frameCount").label == "Frame Count"
    assert desc.BoolParam(name="useGPU").label == "Use GPU"


def test_label_auto_generated_from_snake_case():
    """Label should be auto-generated from snake_case attribute names."""
    assert desc.StringParam(name="input_path").label == "Input Path"
    assert desc.FloatParam(name="min_value").label == "Min Value"


def test_explicit_label_overrides_auto_generated():
    """An explicitly provided label should take precedence over the auto-generated one."""
    attr = desc.File(name="outputFile", label="My Custom Label")
    assert attr.label == "My Custom Label"


def test_explicit_description_preserved():
    """An explicitly provided description should be stored as-is."""
    attr = desc.IntParam(name="count", description="Number of items to process.")
    assert attr.description == "Number of items to process."


# ---------------------------------------------------------------------------
# Tests on attribute runtime instances (require a Graph / node)
# ---------------------------------------------------------------------------

class TestInputParamDefaults:
    """Input params with no explicit value should use the type's zero/empty default."""

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithMinimalInputs)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithMinimalInputs)

    @pytest.fixture
    def node(self):
        graph = Graph("")
        return graph.addNewNode(NodeWithMinimalInputs.__name__)

    def test_file_input_default(self, node):
        assert node.fileInput.value == ""

    def test_bool_input_default(self, node):
        assert node.boolInput.value is False

    def test_int_input_default(self, node):
        assert node.intInput.value == 0

    def test_float_input_default(self, node):
        assert node.floatInput.value == 0.0

    def test_string_input_default(self, node):
        assert node.stringInput.value == ""

    def test_color_input_default(self, node):
        assert node.colorInput.value == ""

    def test_choice_input_default(self, node):
        # ChoiceParam with string values → _valueType=str → str() = ""
        assert node.choiceInput.value == ""


class TestOutputParamDynamicValue:
    """Output params created without a default value should be dynamic (None at runtime)."""

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithDynamicOutputsMinimal)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithDynamicOutputsMinimal)

    @pytest.fixture
    def node(self):
        graph = Graph("")
        return graph.addNewNode(NodeWithDynamicOutputsMinimal.__name__)

    def test_output_desc_is_dynamic(self, node):
        assert node.fileOutput.desc.isDynamicValue is True
        assert node.boolOutput.desc.isDynamicValue is True
        assert node.intOutput.desc.isDynamicValue is True
        assert node.floatOutput.desc.isDynamicValue is True
        assert node.stringOutput.desc.isDynamicValue is True

    def test_file_output_value_is_none(self, node):
        assert node.fileOutput.value is None

    def test_bool_output_value_is_none(self, node):
        assert node.boolOutput.value is None

    def test_int_output_value_is_none(self, node):
        assert node.intOutput.value is None

    def test_float_output_value_is_none(self, node):
        assert node.floatOutput.value is None

    def test_string_output_value_is_none(self, node):
        assert node.stringOutput.value is None
