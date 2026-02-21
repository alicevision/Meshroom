from meshroom.core.graph import Graph
from meshroom.core.desc.attribute import _labelFromName, StringParam, IntParam, FloatParam, BoolParam, File, ListAttribute, GroupAttribute
import pytest

import logging
logger = logging.getLogger('test')

valid3DExtensionFiles = [(f'test.{ext}', True) for ext in ('obj', 'stl', 'fbx', 'gltf', 'abc', 'ply')]
invalid3DExtensionFiles = [(f'test.{ext}', False) for ext in ('', 'exe', 'jpg', 'png', 'py')]

valid2DSemantics= [(semantic, True) for semantic in ('image', 'imageList', 'sequence')]
invalid2DSemantics = [(semantic, False) for semantic in ('3d', '', 'multiline', 'color/hue')]


def test_attribute_retrieve_linked_input_and_output_attributes():
    """
    Check that an attribute can retrieve the linked input and output attributes
    """

    # n0 -- n1 -- n2
    #   \          \
    #    ---------- n3

    g = Graph('')
    n0 = g.addNewNode('Ls', input='')
    n1 = g.addNewNode('Ls', input=n0.output)
    n2 = g.addNewNode('Ls', input=n1.output)
    n3 = g.addNewNode('AppendFiles', input=n1.output, input2=n2.output)

    # check that the attribute can retrieve its linked input attributes

    assert n0.output.hasAnyOutputLinks
    assert not n3.output.hasAnyOutputLinks

    assert len(n0.input.allInputLinks) == 0
    assert len(n1.input.allInputLinks) == 1
    assert n1.input.allInputLinks[0] == n0.output

    assert len(n1.output.allOutputLinks) == 2

    assert n1.output.allOutputLinks[0] == n2.input
    assert n1.output.allOutputLinks[1] == n3.input

    n0.graph = None

    # Bounding cases
    assert not n0.output.hasAnyOutputLinks
    assert len(n0.input.allInputLinks) == 0
    assert len(n0.output.allOutputLinks) == 0


@pytest.mark.parametrize("givenFile,expected", valid3DExtensionFiles + invalid3DExtensionFiles)
def test_attribute_is3D_file_extensions(givenFile, expected):
    """
    Check what makes an attribute a valid 3d media
    """

    g = Graph('')
    n0 = g.addNewNode('Ls', input='')

    # Given
    assert not n0.input.is3dDisplayable

    # When
    n0.input.value = givenFile

    # Then
    assert n0.input.is3dDisplayable == expected


def test_attribute_i3D_by_description_semantic():
    """ """

    # Given
    g = Graph('')
    n0 = g.addNewNode('Ls', input='')

    assert not n0.output.is3dDisplayable

    # When
    n0.output.desc._semantic = "3d"

    # Then
    assert n0.output.is3dDisplayable


@pytest.mark.parametrize("givenSemantic,expected", valid2DSemantics + invalid2DSemantics)
def test_attribute_is2D_file_semantic(givenSemantic, expected):
    """
    Check what makes an attribute a valid 2d media
    """

    g = Graph('')
    n0 = g.addNewNode('Ls', input='')

    # Given
    n0.input.desc._semantic = ""
    assert not n0.input.is2dDisplayable

    # When
    n0.input.desc._semantic = givenSemantic

    # Then
    assert n0.input.is2dDisplayable == expected


@pytest.mark.parametrize("name,expected_label", [
    ("myAttributeName", "My Attribute Name"),
    ("my_attribute_name", "My Attribute Name"),
    ("input", "Input"),
    ("outputMesh", "Output Mesh"),
    ("nbPoints", "Nb Points"),
    ("imageWidth", "Image Width"),
])
def test_label_from_name(name, expected_label):
    """Check that _labelFromName converts camelCase/snake_case names to title case labels."""
    assert _labelFromName(name) == expected_label


def test_attribute_label_auto_generated_when_not_provided():
    """Check that label is auto-generated from name when not explicitly provided."""
    attr = StringParam(name="myAttributeName", value="")
    assert attr.label == "My Attribute Name"

    attr = IntParam(name="nb_points", value=0)
    assert attr.label == "Nb Points"


def test_attribute_label_uses_explicit_value_when_provided():
    """Check that an explicitly provided label is used as-is."""
    attr = StringParam(name="myAttributeName", label="Custom Label", value="")
    assert attr.label == "Custom Label"


def test_attribute_description_defaults_to_empty_string_when_not_provided():
    """Check that description defaults to empty string when not explicitly provided."""
    attr = StringParam(name="myAttribute", value="")
    assert attr.description == ""


def test_attribute_description_uses_explicit_value_when_provided():
    """Check that an explicitly provided description is used as-is."""
    attr = StringParam(name="myAttribute", description="My description.", value="")
    assert attr.description == "My description."
