from pathlib import Path
import tempfile

import pytest

from meshroom.core.graph import Graph


@pytest.fixture
def graphWithIsolatedCache():
    """
    Yield a Graph instance using a unique temporary cache directory.

    Can be used for testing graph computation in isolation, without having to save the graph to disk.
    """
    with tempfile.TemporaryDirectory() as cacheDir:
        graph = Graph("")
        graph.cacheDir = cacheDir
        yield graph

    
@pytest.fixture
def graphSavedOnDisk():
    """
    Yield a Graph instance saved in a unique temporary folder.

    Can be used for testing graph IO and computation in isolation.
    """
    with tempfile.TemporaryDirectory() as cacheDir:
        graph = Graph("")
        graph.save(Path(cacheDir) / "test_graph.mg")
        yield graph
