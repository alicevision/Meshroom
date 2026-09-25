from pathlib import Path

from meshroom.env import meshroomFolder
from meshroom.core.files import isSafeFolderName


# The folder holding the user's local plugin registries and locally installed plugins.
meshroomPluginsFolder = Path(meshroomFolder) / "plugins"

# Prefix an entry directly under "meshroomPluginsFolder" as internal scratch state.
# (e.g. a backup folder or a temporary file) not an installed plugin or a registry file.
# initPlugins() should skips such entries.
meshroomPluginsInternalPrefix = "__"


def isValidPluginName(name) -> bool:
    """
    Return whether "name" is safe to use as a plugin's folder name directly under
    "meshroomPluginsFolder".
    """
    return isSafeFolderName(name) and not name.startswith(meshroomPluginsInternalPrefix)
