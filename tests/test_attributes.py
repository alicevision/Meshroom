from meshroom.core.graph import Graph
from meshroom.core.desc import (
    IntParam, FloatParam, BoolParam, StringParam, 
    ChoiceParam, File, ListAttribute, GroupAttribute
)
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


def test_attribute_label_auto_generation():
    """
    Test that attribute labels are auto-generated from attribute names when not provided
    """
    # Test various naming conventions
    test_cases = [
        ('myAttribute', 'My Attribute'),
        ('some_attribute', 'Some Attribute'),
        ('MyAttribute', 'My Attribute'),
        ('ALLCAPS', 'Allcaps'),
        ('simple', 'Simple'),
        ('test_with_multiple_words', 'Test With Multiple Words'),
        ('camelCaseTest', 'Camel Case Test'),
    ]
    
    for attr_name, expected_label in test_cases:
        attr = IntParam(name=attr_name, value=0)
        assert attr.label == expected_label, f"Failed for {attr_name}: expected '{expected_label}', got '{attr.label}'"


def test_attribute_label_explicit():
    """
    Test that explicit labels are preserved
    """
    attr = IntParam(name='myAttribute', label='Custom Label', value=0)
    assert attr.label == 'Custom Label'


def test_attribute_description_defaults_to_empty_string():
    """
    Test that description defaults to empty string when None
    """
    attr = IntParam(name='myParam', value=0)
    assert attr.description == ''


def test_attribute_description_explicit():
    """
    Test that explicit descriptions are preserved
    """
    attr = IntParam(name='myParam', description='Custom description', value=0)
    assert attr.description == 'Custom description'


def test_choiceparam_requires_values():
    """
    Test that ChoiceParam raises ValueError when values is None
    """
    with pytest.raises(ValueError, match="ChoiceParam 'myChoice' requires 'values' parameter to be set, cannot be None"):
        ChoiceParam(name='myChoice', value='a', values=None)


def test_choiceparam_with_valid_values():
    """
    Test that ChoiceParam works correctly when values is provided
    """
    attr = ChoiceParam(name='myChoice', value='a', values=['a', 'b', 'c'])
    assert attr.values == ['a', 'b', 'c']
    assert attr.label == 'My Choice'
    assert attr.description == ''


def test_various_param_types_default_label_and_description():
    """
    Test that all parameter types support default label and description
    """
    # IntParam
    int_param = IntParam(name='intValue', value=5)
    assert int_param.label == 'Int Value'
    assert int_param.description == ''
    
    # FloatParam
    float_param = FloatParam(name='floatValue', value=3.14)
    assert float_param.label == 'Float Value'
    assert float_param.description == ''
    
    # BoolParam
    bool_param = BoolParam(name='enableFeature', value=True)
    assert bool_param.label == 'Enable Feature'
    assert bool_param.description == ''
    
    # StringParam
    string_param = StringParam(name='textInput', value='hello')
    assert string_param.label == 'Text Input'
    assert string_param.description == ''
    
    # File
    file_param = File(name='inputFile', value='')
    assert file_param.label == 'Input File'
    assert file_param.description == ''


def test_list_attribute_default_label_and_description():
    """
    Test that ListAttribute supports default label and description
    """
    elem_desc = IntParam(name='elem', value=0)
    list_attr = ListAttribute(elementDesc=elem_desc, name='myList')
    assert list_attr.label == 'My List'
    assert list_attr.description == ''


def test_group_attribute_default_label_and_description():
    """
    Test that GroupAttribute supports default label and description
    """
    items = [
        IntParam(name='x', value=0),
        IntParam(name='y', value=0)
    ]
    group_attr = GroupAttribute(items=items, name='myGroup')
    assert group_attr.label == 'My Group'
    assert group_attr.description == ''
