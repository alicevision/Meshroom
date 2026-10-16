from pathlib import Path

from meshroom.env import EnvVar, getInstallFolder, meshroomFolder
from meshroom.core.files import isSafeFolderName


def getLocalPluginsFolder() -> Path:
    """
    Return the folder holding the user's local plugin registries and locally installed plugins:
    "MESHROOM_LOCAL_PLUGINS_PATH" if set, else the "plugins" folder in the Meshroom installation
    folder (the repository root when running from sources).
    """
    folder = EnvVar.get(EnvVar.MESHROOM_LOCAL_PLUGINS_PATH)
    if folder:
        return Path(folder)
    return Path(getInstallFolder() or Path(meshroomFolder).parent) / "plugins"


def isValidPluginName(name) -> bool:
    """
    Return whether "name" is safe to use as a plugin's folder name directly under
    "meshroomPluginsFolder".
    """
    return isSafeFolderName(name) and not name.startswith(meshroomPluginsInternalPrefix)


# The folder holding the user's local plugin registries and locally installed plugins.
meshroomPluginsFolder = getLocalPluginsFolder()

# Prefix an entry directly under "meshroomPluginsFolder" as internal scratch state.
# (e.g. a backup folder or a temporary file) not an installed plugin or a registry file.
# initPlugins() should skips such entries.
meshroomPluginsInternalPrefix = "__"
