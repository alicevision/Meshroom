""" Presentation of the pipeline templates metadata (header "templateInfo"): category colors, icons and labels.

Qt-free so that it can be unit tested without a UI.
"""
import colorsys
import json
import logging
import math
import os
import re
import zlib
from typing import Dict, Iterable, List, Optional

from meshroom.env import meshroomFolder
from meshroom.ui.components.materialIcons import readMaterialIcons

# Names of all the MaterialIcons, read from the icon font
MATERIAL_ICONS = list(readMaterialIcons())
# Built-in category colors ({category name: "#RRGGBB"}), matched case-insensitively
CATEGORY_COLORS_FILE = os.path.join(meshroomFolder, "ui", "config", "templateCategoryColors.json")

UNCATEGORIZED_COLOR = "#6A6C71"
# Icons listed while nothing is searched, relevant to pipelines (those missing from MaterialIcons are skipped)
DEFAULT_ICONS = (
    "photo_camera", "camera", "videocam", "movie", "view_in_ar", "_3d_rotation", "_360",
    "panorama", "panorama_photosphere", "panorama_fish_eye", "hdr_on", "filter_hdr", "light_mode", "flash_on",
    "lens", "grid_on", "straighten", "palette", "raw_on", "texture", "image",
)
# Fields edited by the Save As Template dialog; any other key of an existing templateInfo is kept
EDITABLE_FIELDS = ("label", "category", "icon", "description")

# Homepage pipeline list: rows shown per category before "Show all", and columns a category can take
CATEGORY_MAX_ROWS = 6
CATEGORY_MAX_SPAN = 2

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


def groupByCategory(templates: Iterable[dict], builtinCategories: Iterable[str]) -> List[dict]:
    """ Group the `templates` ({"name", "category", "color", ...}) by category, case-insensitively.

    Categories are sorted with the `builtinCategories` first in their order (and spelling), then the others by name, and the
    uncategorised templates last. Templates are sorted by "label" (or "name" without label).

    Returns:
        list: [{"name": category name ("" for uncategorised), "color": its color, "templates": [template, ...]}]
    """
    groups = {}
    for template in templates:
        category = (template.get("category") or "").strip()
        groups.setdefault(category.lower(), {"name": category, "color": template.get("color", UNCATEGORIZED_COLOR),
                                             "templates": []})["templates"].append(template)
    builtinNames = [c.strip() for c in builtinCategories]
    builtin = [c.lower() for c in builtinNames]
    for key, group in groups.items():
        if key in builtin:
            group["name"] = builtinNames[builtin.index(key)]

    def categoryKey(key):
        if not key:
            return (2, 0, "")
        if key in builtin:
            return (0, builtin.index(key), key)
        return (1, 0, key)

    result = [groups[key] for key in sorted(groups, key=categoryKey)]
    for group in result:
        group["templates"].sort(key=lambda t: (t.get("label") or t.get("name", "")).lower())
    return result


def layoutCategories(categories: Iterable[dict], columns: int, expanded: Iterable[str] = (),
                     maxRows: int = CATEGORY_MAX_ROWS, maxSpan: int = CATEGORY_MAX_SPAN) -> List[List[dict]]:
    """ Lay out the category groups of `groupByCategory` in rows of `columns` columns, so that the pipelines use the
    width instead of making one tall column.

    Each category asks for ceil(count / maxRows) columns (at most `maxSpan`), the categories are packed in order into rows,
    and the free columns at the end of a row go to the category still hiding the most pipelines, else to the tallest one.
    A category with more pipelines than `span * maxRows` shows one pipeline less, for a "Show remaining" item.
    When categories are named in `expanded` (case-insensitive), only those are laid out, each on a whole row with all
    their pipelines.

    Returns:
        list: rows of [{"name", "color", "count", "templates": templates shown, "remaining": pipelines not shown,
              "span": columns, "rows": rows, "expanded": bool, "truncated": bool}]
    """
    columns = max(1, columns)
    maxRows = max(2, maxRows)
    expanded = {name.lower() for name in expanded}
    if any(category["name"].lower() in expanded for category in categories):
        categories = [category for category in categories if category["name"].lower() in expanded]
    blocks = []
    for category in categories:
        count = len(category["templates"])
        isExpanded = category["name"].lower() in expanded
        span = columns if isExpanded else max(1, min(maxSpan, columns, math.ceil(count / maxRows)))
        blocks.append({"category": category, "count": count, "span": span, "expanded": isExpanded})

    rows, row, used = [], [], 0
    for block in blocks:
        if row and used + block["span"] > columns:
            rows.append(row)
            row, used = [], 0
        row.append(block)
        used += block["span"]
    if row:
        rows.append(row)

    for row in rows:
        free = columns - sum(block["span"] for block in row)
        while free > 0:
            growable = [b for b in row if not b["expanded"] and b["span"] < b["count"]]
            if not growable:
                break
            # Most hidden pipelines first, then the tallest block
            best = max(growable, key=lambda b: (b["count"] - b["span"] * maxRows, math.ceil(b["count"] / b["span"])))
            best["span"] += 1
            free -= 1

    result = []
    for row in rows:
        resultRow = []
        for block in row:
            templates, count, span = block["category"]["templates"], block["count"], block["span"]
            truncated = not block["expanded"] and count > span * maxRows
            shown = templates[:span * maxRows - 1] if truncated else templates
            resultRow.append({
                "name": block["category"]["name"],
                "color": block["category"]["color"],
                "count": count,
                "templates": shown,
                "remaining": count - len(shown),
                "span": span,
                "rows": maxRows if truncated else max(1, math.ceil(count / span)),
                "expanded": block["expanded"],
                "truncated": truncated,
            })
        result.append(resultRow)
    return result


def defaultTemplateLabel(key: str) -> str:
    """ Return the label derived from the template key, split on capital letters (e.g. "panoramaHdr" -> "Panorama Hdr"). """
    if not key:
        return ""
    key = key[0].upper() + key[1:]
    return " ".join(re.findall("[A-Z][^A-Z]*", key)) or key


def updatedTemplateInfo(currentInfo: Optional[dict], editedInfo: Optional[dict]) -> dict:
    """ Return the templateInfo to save: `currentInfo` updated with the editable fields of `editedInfo`.

    Text values are stripped and empty fields are dropped, so a template without any info stores none.
    Keys that are not edited by the dialog are kept from `currentInfo`.
    """
    info = {k: v for k, v in (currentInfo or {}).items() if k not in EDITABLE_FIELDS}
    for field in EDITABLE_FIELDS:
        value = (editedInfo or {}).get(field)
        value = value.strip() if isinstance(value, str) else value
        if value:
            info[field] = value
    return info


def searchIcons(query: str, names: Iterable[str] = MATERIAL_ICONS,
                defaults: Iterable[str] = DEFAULT_ICONS) -> List[str]:
    """ Return the icon `names` matching all the words of `query` (case-insensitive, "_" and spaces are equivalent).

    `names` defaults to all the MaterialIcons. Names starting with the query come first. An empty query returns the `defaults` that are in `names`.
    """
    query = (query or "").strip().lower().replace("_", " ")
    words = query.split()
    if not words:
        available = set(names)
        return [name for name in defaults if name in available]
    matches = [name for name in names if all(word in name.lower().replace("_", " ") for word in words)]
    return sorted(matches, key=lambda name: not name.lower().replace("_", " ").lstrip(" ").startswith(query))
