import logging
from pathlib import Path
import shutil

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

# The registries shipped with Meshroom, copied into "meshroomPluginsFolder" on first run.
meshroomRegistriesFolder = Path(meshroomFolder) / "core" / "plugins" / "registries"


def initLocalPluginsFolder(pluginsFolder: Path = meshroomPluginsFolder,
                           registriesFolder: Path = meshroomRegistriesFolder):
    """
    Create the local plugins folder on first run, seeded with the registries shipped with Meshroom.
    An existing folder is left untouched, so that a registry removed by the user is not restored.

    Args:
        pluginsFolder: the local plugins folder to create.
        registriesFolder: the folder holding the registry files to copy into it.
    """
    if pluginsFolder.exists():
        return
    try:
        pluginsFolder.mkdir(parents=True)
        for registryPath in registriesFolder.glob("*.json"):
            shutil.copy2(registryPath, pluginsFolder / registryPath.name)
    except OSError as exc:
        logging.warning(f"Cannot initialize the local plugins folder '{pluginsFolder}':\n{exc}")
