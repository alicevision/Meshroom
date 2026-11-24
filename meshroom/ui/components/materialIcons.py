"""
MaterialIcons QML singleton, generated at startup from the icons read from the icon font.

The font has no list of icon names: each icon is a ligature (GSUB table) that turns the letters of its name
into its glyph, and the character map (cmap table) gives the codepoint of each glyph.
TrueType tables are big-endian, and all the offsets below are relative to the start of their parent table.
"""

import base64
import json
import logging
import os
import struct

from PySide6.QtCore import QUrl
from PySide6.QtQml import qmlRegisterSingletonType

from meshroom.env import meshroomFolder

MATERIAL_ICONS_FONT = os.path.join(meshroomFolder, "ui", "qml", "MaterialIcons", "MaterialIcons-Regular.ttf")
# Family of the icon font, used if it cannot be read from the font file
DEFAULT_FONT_FAMILY = "Material Icons"

# Icon names that are JavaScript keywords or clash with QtObject properties
RENAMED_ICONS = {
    "delete": "delete_",
    "class": "class_",
    "opacity": "opacity_",
    "transform": "transform_",
    "print": "print_",
    "public": "public_",
    "password": "pwd",
    "wifi_password": "wifi_pwd",
    "try": "try_",
}


def _u16(data: bytes, offset: int) -> int:
    """ Read an unsigned 16-bit integer. """
    return struct.unpack_from(">H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    """ Read an unsigned 32-bit integer. """
    return struct.unpack_from(">I", data, offset)[0]


def _readCodepoints(data: bytes, cmap: int) -> dict:
    """ Read the character map of the font.

    Args:
        data: the content of the font file.
        cmap: offset of the cmap table.

    Returns:
        {glyph id: lowest codepoint drawn with this glyph}.
    """
    codepoints = {}
    # cmap header: version (u16), number of subtables (u16), then one 8-byte record per subtable
    for i in range(_u16(data, cmap + 2)):
        platformId, encodingId, offset = struct.unpack_from(">HHI", data, cmap + 4 + 8 * i)
        subtable = cmap + offset
        # Windows (3) / Unicode full repertoire (10) encoding, stored in format 12
        # shortcut: only reads the (3, 10) format 12 subtable, add format 4 if a font without one is ever bundled
        if (platformId, encodingId) != (3, 10) or _u16(data, subtable) != 12:
            continue
        # Format 12: format, reserved (u16), length, language, number of groups (u32),
        # then groups of consecutive codepoints mapped to consecutive glyphs: start, end, start glyph (u32)
        for g in range(_u32(data, subtable + 12)):
            start, end, startGlyph = struct.unpack_from(">III", data, subtable + 16 + 12 * g)
            for codepoint in range(start, end + 1):
                codepoints.setdefault(startGlyph + codepoint - start, codepoint)
    return codepoints


def _readCoverage(data: bytes, coverage: int) -> list:
    """ Read an OpenType coverage table, the list of glyphs a substitution applies to.

    Args:
        data: the content of the font file.
        coverage: offset of the coverage table.

    Returns:
        the glyph ids, in coverage index order.
    """
    # Format 1: format, glyph count (u16), then the glyph ids (u16)
    if _u16(data, coverage) == 1:
        return [_u16(data, coverage + 4 + 2 * i) for i in range(_u16(data, coverage + 2))]
    # Format 2: format, range count (u16), then ranges of consecutive glyphs: start, end, start index (u16)
    glyphs = []
    for i in range(_u16(data, coverage + 2)):
        start, end, _ = struct.unpack_from(">HHH", data, coverage + 4 + 6 * i)
        glyphs.extend(range(start, end + 1))
    return glyphs


def _readLigatures(data: bytes, gsub: int):
    """ Read the ligature substitutions of the font.

    Args:
        data: the content of the font file.
        gsub: offset of the GSUB table.

    Yields:
        (component glyph ids, ligature glyph id) for each ligature: the components are the letters of an icon name,
        the ligature is the glyph of the icon.
    """
    # GSUB header: version (2 * u16), script list, feature list, lookup list offsets (u16)
    lookupList = gsub + _u16(data, gsub + 8)
    # Lookup list: lookup count (u16), then the lookup offsets (u16)
    for i in range(_u16(data, lookupList)):
        lookup = lookupList + _u16(data, lookupList + 2 + 2 * i)
        # Lookup: type, flags, subtable count (u16), then the subtable offsets (u16)
        lookupType = _u16(data, lookup)
        for j in range(_u16(data, lookup + 4)):
            subtable = lookup + _u16(data, lookup + 6 + 2 * j)
            # Extension (type 7): format, type of the actual subtable (u16), 32-bit offset of the actual subtable
            if lookupType == 7:
                lookupType, subtable = _u16(data, subtable + 2), subtable + _u32(data, subtable + 4)
            # Only ligature substitutions (type 4) give icon names
            if lookupType != 4:
                continue
            # Ligature substitution: format, coverage offset, ligature set count (u16), then the ligature set offsets (u16).
            # The coverage lists the first letter of the ligatures, one ligature set per first letter.
            firstGlyphs = _readCoverage(data, subtable + _u16(data, subtable + 2))
            for k, firstGlyph in enumerate(firstGlyphs):
                ligatureSet = subtable + _u16(data, subtable + 6 + 2 * k)
                # Ligature set: ligature count (u16), then the ligature offsets (u16)
                for m in range(_u16(data, ligatureSet)):
                    ligature = ligatureSet + _u16(data, ligatureSet + 2 + 2 * m)
                    # Ligature: ligature glyph, component count (u16), then the components after the first letter (u16)
                    glyph, count = _u16(data, ligature), _u16(data, ligature + 2)
                    yield [firstGlyph] + [_u16(data, ligature + 4 + 2 * c) for c in range(count - 1)], glyph


def readMaterialIcons(path: str = MATERIAL_ICONS_FONT) -> dict:
    """ Read the icons of a ligature icon font.

    Args:
        path: the TrueType font file.

    Returns:
        {name: glyph} sorted by name, the names being valid QML property names
        (see RENAMED_ICONS, and names starting with a digit get a leading underscore).
        A name shared by several glyphs is indexed from its second occurrence, by increasing codepoint.
    """
    with open(path, "rb") as f:
        data = f.read()
    # Table directory: number of tables (u16) at offset 4, then from offset 12 one 16-byte record per table:
    # tag, checksum, offset, length (u32)
    tables = {}
    for i in range(_u16(data, 4)):
        tag, _, offset, _ = struct.unpack_from(">4sIII", data, 12 + 16 * i)
        tables[tag] = offset
    codepoints = _readCodepoints(data, tables[b"cmap"])
    icons = {}
    # Sorted by codepoint, so that the duplicated names are indexed in a stable order
    ligatures = sorted(_readLigatures(data, tables[b"GSUB"]), key=lambda ligature: codepoints[ligature[1]])
    for components, glyph in ligatures:
        # The components are the glyphs of the letters of the name: turn them back into characters
        name = "".join(chr(codepoints[c]) for c in components)
        name = RENAMED_ICONS.get(name, name)
        # QML property names cannot start with a digit (e.g. "3d_rotation" becomes "_3d_rotation")
        if name[0].isdigit():
            name = "_" + name
        # A name shared by several glyphs gets an index from its second occurrence (e.g. "flourescent2")
        uniqueName, index = name, 2
        while uniqueName in icons:
            uniqueName, index = f"{name}{index}", index + 1
        icons[uniqueName] = chr(codepoints[glyph])
    return dict(sorted(icons.items()))


def loadMaterialIconsFont(path: str = MATERIAL_ICONS_FONT) -> str:
    """ Load the icon font in the application and return its family name. A QGuiApplication must exist. """
    # Imported here so that reading the icons does not need PySide6.QtGui (and libEGL)
    from PySide6.QtGui import QFontDatabase
    fontId = QFontDatabase.addApplicationFont(path)
    families = QFontDatabase.applicationFontFamilies(fontId) if fontId >= 0 else []
    if not families:
        logging.warning(f"Could not load the MaterialIcons font ({path}).")
        return DEFAULT_FONT_FAMILY
    return families[0]


def registerMaterialIcons():
    """ Load the icon font and register the MaterialIcons singleton in the MaterialIcons QML module (2.2):
    `MaterialIcons.<name>` is the glyph of an icon and `MaterialIcons.fontFamily` the family of the icon font.
    The singleton is a QtObject with one readonly property per icon, so its properties are looked up as fast
    as the ones of a singleton written in a QML file. A QGuiApplication must exist.
    """
    glyphs = {"fontFamily": loadMaterialIconsFont(), **readMaterialIcons()}
    # json.dumps gives valid JS string literals, including surrogate pairs beyond the Basic Multilingual Plane
    properties = "\n".join(f"    readonly property string {name}: {json.dumps(glyph)}" for name, glyph in glyphs.items())
    source = f"pragma Singleton\nimport QtQml\n\nQtObject {{\n{properties}\n}}\n"
    # A data URL lets QML compile the generated source without writing it to a file
    url = QUrl("data:text/plain;base64," + base64.b64encode(source.encode()).decode())
    qmlRegisterSingletonType(url, "MaterialIcons", 2, 2, "MaterialIcons")
