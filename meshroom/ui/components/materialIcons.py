""" MaterialIcons exposed to QML: the icon font family and one property per icon, built from a Python dictionary. """
import logging
import os

from PySide6.QtCore import QObject
from PySide6.QtGui import QFontDatabase
from PySide6.QtQml import QQmlPropertyMap

from meshroom.env import meshroomFolder
from meshroom.ui.components.materialIconsData import MATERIAL_ICONS

MATERIAL_ICONS_FONT = os.path.join(meshroomFolder, "ui", "qml", "MaterialIcons", "MaterialIcons-Regular.ttf")
# Family of the icon font, used if it cannot be read from the font file
DEFAULT_FONT_FAMILY = "Material Icons"


def loadMaterialIconsFont(path: str = MATERIAL_ICONS_FONT) -> str:
    """ Load the icon font in the application and return its family name. A QGuiApplication must exist. """
    fontId = QFontDatabase.addApplicationFont(path)
    families = QFontDatabase.applicationFontFamilies(fontId) if fontId >= 0 else []
    if not families:
        logging.warning(f"Could not load the MaterialIcons font ({path}).")
        return DEFAULT_FONT_FAMILY
    return families[0]


def createMaterialIcons(parent: QObject) -> QQmlPropertyMap:
    """ Return the MaterialIcons map exposed to QML: `MaterialIcons.<name>` is the glyph of an icon
    and `MaterialIcons.fontFamily` the family of the icon font.

    Args:
        parent: owner of the map, which keeps it alive while QML uses it.
    """
    # create() rather than the constructor, which PySide marks as deprecated
    icons = QQmlPropertyMap.create(parent)
    icons.insert({"fontFamily": loadMaterialIconsFont(), **MATERIAL_ICONS})
    return icons
