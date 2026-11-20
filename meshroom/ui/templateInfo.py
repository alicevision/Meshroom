""" Presentation of the pipeline templates metadata (header "templateInfo"): category colors, icons and labels.

Qt-free so that it can be unit tested without a UI.
"""
import colorsys
import json
import logging
import os
import re
import zlib
from typing import Dict, Iterable, List, Optional

from meshroom.env import meshroomFolder

# Built-in category colors ({category name: "#RRGGBB"}), matched case-insensitively
CATEGORY_COLORS_FILE = os.path.join(meshroomFolder, "ui", "config", "templateCategoryColors.json")
MATERIAL_ICONS_FILE = os.path.join(meshroomFolder, "ui", "qml", "MaterialIcons", "MaterialIcons.qml")

UNCATEGORIZED_COLOR = "#6A6C71"
# Icons listed while nothing is searched, relevant to pipelines (those missing from MaterialIcons are skipped)
DEFAULT_ICONS = (
    "photo_camera", "camera", "videocam", "movie", "view_in_ar", "_3d_rotation", "_360",
    "panorama", "panorama_photosphere", "panorama_fish_eye", "hdr_on", "filter_hdr", "light_mode", "flash_on",
    "lens", "grid_on", "straighten", "palette", "raw_on", "texture", "image",
)
# Fields edited by the Save As Template dialog; any other key of an existing templateInfo (e.g. "order") is kept
EDITABLE_FIELDS = ("label", "category", "icon", "description")

# Saturation and lightness of the hashed category colors
HASH_SATURATION = 0.65
HASH_LIGHTNESS = 0.62


def loadCategoryColors(path: str = CATEGORY_COLORS_FILE) -> Dict[str, str]:
    """ Return the built-in category colors {category name: color} read from the JSON file at `path`. """
    try:
        with open(path) as file:
            colors = json.load(file)
    except (OSError, ValueError) as e:
        logging.warning(f"Could not read the template category colors ({path}): {e}")
        return {}
    if not isinstance(colors, dict):
        logging.warning(f"Invalid template category colors ({path}): expected a JSON object.")
        return {}
    return {str(name): str(color) for name, color in colors.items()}


def hashedCategoryColor(name: str) -> str:
    """ Return a color computed from the lower-case `name`: the same name gets the same color on every machine.

    The hue is crc32 of the UTF-8 lower-case name modulo 360, with a fixed saturation and lightness.
    """
    hue = zlib.crc32(name.strip().lower().encode("utf-8")) % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, HASH_LIGHTNESS, HASH_SATURATION)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def categoryColor(name: Optional[str], colors: Optional[Dict[str, str]] = None) -> str:
    """ Return the color of the category `name`.

    Args:
        name: the category name; empty or None for an uncategorised template.
        colors: the built-in colors {category name: color}, looked up case-insensitively first.

    Returns:
        str: the color from `colors` if listed, otherwise the color hashed from the lower-case name.
    """
    name = (name or "").strip()
    if not name:
        return UNCATEGORIZED_COLOR
    lowerName = name.lower()
    for key, color in (colors or {}).items():
        if key.strip().lower() == lowerName:
            return color
    return hashedCategoryColor(name)


def mergeCategories(*categoryLists: Iterable[str]) -> List[str]:
    """ Merge category names, ignoring empty names and case-insensitive duplicates (the first spelling is kept). """
    merged = {}
    for categories in categoryLists:
        for category in categories:
            category = category.strip() if isinstance(category, str) else ""
            if category and category.lower() not in merged:
                merged[category.lower()] = category
    return list(merged.values())


def defaultTemplateLabel(key: str) -> str:
    """ Return the label derived from the template key, split on capital letters (e.g. "panoramaHdr" -> "Panorama Hdr"). """
    if not key:
        return ""
    key = key[0].upper() + key[1:]
    return " ".join(re.findall("[A-Z][^A-Z]*", key)) or key


def updatedTemplateInfo(currentInfo: Optional[dict], editedInfo: Optional[dict]) -> dict:
    """ Return the templateInfo to save: `currentInfo` updated with the editable fields of `editedInfo`.

    Text values are stripped and empty fields are dropped, so a template without any info stores none.
    Keys that are not edited by the dialog (e.g. "order") are kept from `currentInfo`.
    """
    info = {k: v for k, v in (currentInfo or {}).items() if k not in EDITABLE_FIELDS}
    for field in EDITABLE_FIELDS:
        value = (editedInfo or {}).get(field)
        value = value.strip() if isinstance(value, str) else value
        if value:
            info[field] = value
    return info


def materialIconNames(path: str = MATERIAL_ICONS_FILE) -> List[str]:
    """ Return the names of the icons declared in the MaterialIcons QML singleton at `path`. """
    try:
        with open(path, encoding="utf-8") as file:
            content = file.read()
    except OSError as e:
        logging.warning(f"Could not read the MaterialIcons names ({path}): {e}")
        return []
    names = re.findall(r'readonly property string (\w+): "\\u', content)
    return names


def searchIcons(names: Iterable[str], query: str, defaults: Iterable[str] = DEFAULT_ICONS) -> List[str]:
    """ Return the icon `names` matching all the words of `query` (case-insensitive, "_" and spaces are equivalent).

    Names starting with the query come first. An empty query returns the `defaults` that are in `names`.
    """
    query = (query or "").strip().lower().replace("_", " ")
    words = query.split()
    if not words:
        available = set(names)
        return [name for name in defaults if name in available]
    matches = [name for name in names if all(word in name.lower().replace("_", " ") for word in words)]
    return sorted(matches, key=lambda name: not name.lower().replace("_", " ").lstrip(" ").startswith(query))
