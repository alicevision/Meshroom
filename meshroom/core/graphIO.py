from enum import Enum
from typing import Union

from meshroom.core import Version


class GraphIO:
    """Centralize Graph file keys and IO version."""

    __version__ = "2.0"

    class Keys(object):
        """File Keys."""

        # Doesn't inherit enum to simplify usage (GraphIO.Keys.XX, without .value)
        Header = "header"
        NodesVersions = "nodesVersions"
        ReleaseVersion = "releaseVersion"
        FileVersion = "fileVersion"
        Graph = "graph"

    class Features(Enum):
        """File Features."""

        Graph = "graph"
        Header = "header"
        NodesVersions = "nodesVersions"
        PrecomputedOutputs = "precomputedOutputs"
        NodesPositions = "nodesPositions"

    @staticmethod
    def getFeaturesForVersion(fileVersion: Union[str, Version]) -> tuple["GraphIO.Features",...]:
        """Return the list of supported features based on a file version.

        Args:
            fileVersion (str, Version): the file version

        Returns:
            tuple of GraphIO.Features: the list of supported features
        """
        if isinstance(fileVersion, str):
            fileVersion = Version(fileVersion)

        features = [GraphIO.Features.Graph]
        if fileVersion >= Version("1.0"):
            features += [
                GraphIO.Features.Header,
                GraphIO.Features.NodesVersions,
                GraphIO.Features.PrecomputedOutputs,
            ]

        if fileVersion >= Version("1.1"):
            features += [GraphIO.Features.NodesPositions]

        return tuple(features)

