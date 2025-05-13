from meshroom.core.graph import Graph
import pytest

import logging
logger = logging.getLogger('test')

valid3DExtensionFiles = [(f'test.{ext}', True) for ext in ('obj', 'stl', 'fbx', 'gltf', 'abc', 'ply')]
invalid3DExtensionFiles = [(f'test.{ext}', False) for ext in ('', 'exe', 'jpg', 'png', 'py')]

valid2DSemantics= [(semantic, True) for semantic in ('image', 'imageList', 'sequence')]
invalid2DSemantics = [(semantic, False) for semantic in ('3d', '', 'multiline', 'color/hue')]


@pytest.mark.parametrize("givenFile,expected", valid3DExtensionFiles + invalid3DExtensionFiles)
def test_attribute_is3D_file_extensions(givenFile, expected):
    """
    Check what makes an attribute a valid 3d media
    """

    g = Graph('')
    n0 = g.addNewNode('Ls', input='')

    # Given
    assert not n0.input.is3D

    # When
    n0.input.value = givenFile

    # Then
    assert n0.input.is3D == expected


def test_attribute_i3D_by_description_semantic():
    """ """

    # Given
    g = Graph('')
    n0 = g.addNewNode('Ls', input='')  

    assert not n0.output.is3D

    # When
    n0.output.desc._semantic = "3d"

    # Then
    assert n0.output.is3D

@pytest.mark.parametrize("givenSemantic,expected", valid2DSemantics + invalid2DSemantics)
def test_attribute_is2D_file_semantic(givenSemantic, expected):
    """
    Check what makes an attribute a valid 2d media
    """

    g = Graph('')
    n0 = g.addNewNode('Ls', input='')

    # Given
    n0.input.desc._semantic = ""
    assert not n0.input.is2D

    # When
    n0.input.desc._semantic = givenSemantic

    # Then
    assert n0.input.is2D == expected