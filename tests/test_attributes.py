from meshroom.core.graph import Graph


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
    assert len(n0.input.getInputAttributes()) == 0
    assert len(n1.input.getInputAttributes()) == 1
    assert n1.input.getInputAttributes()[0] == n0.output
    
    assert len(n1.output.getOutputAttributes()) == 2
    
    assert n1.output.getOutputAttributes()[0] == n2.input
    assert n1.output.getOutputAttributes()[1] == n3.input

    