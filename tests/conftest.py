from pathlib import Path
import tempfile

import pytest

from meshroom.core.graph import Graph


@pytest.fixture
def graphSavedOnDisk():
    """
    Yield a Graph instance saved in a unique temporary folder.

    Can be used for testing graph IO and computation in isolation.
    """
    with tempfile.TemporaryDirectory() as cacheDir:
        graph = Graph()
        graph.saveAsTemp(cacheDir)
        yield graph
