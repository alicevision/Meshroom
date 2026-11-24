import os
import re

import pytest

from meshroom.ui.components.materialIcons import MATERIAL_ICONS_FONT, readMaterialIcons

MATERIAL_ICONS = readMaterialIcons()


def test_material_icons_names_are_qml_identifiers():
    for name in MATERIAL_ICONS:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name), name
    # Names clashing with JavaScript keywords or numeric literals are renamed
    for name in ("delete", "class", "try", "3d_rotation", "123"):
        assert name not in MATERIAL_ICONS
    for name in ("delete_", "class_", "try_", "_3d_rotation", "_123"):
        assert name in MATERIAL_ICONS


def test_material_icons_glyphs():
    assert all(len(glyph) == 1 for glyph in MATERIAL_ICONS.values())
    assert MATERIAL_ICONS["camera"] == "\ue3af"
    # Codepoints beyond the Basic Multilingual Plane are kept whole
    assert MATERIAL_ICONS["goat"] == "\U0010fffd"


def test_read_material_icons_from_font():
    icons = readMaterialIcons(MATERIAL_ICONS_FONT)
    # Every glyph of the font with a ligature is read, sorted by name
    assert len(icons) == 2234
    assert list(icons) == sorted(icons)


def test_register_material_icons_singleton():
    # Registering the singleton loads the icon font, which needs PySide6.QtGui (and libEGL)
    pytest.importorskip("PySide6.QtGui", exc_type=ImportError)
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QFontDatabase, QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from meshroom.ui.components.materialIcons import registerMaterialIcons

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    # The family falls back to "Material Icons" when the font cannot be loaded: check the font file itself
    assert QFontDatabase.addApplicationFont(MATERIAL_ICONS_FONT) >= 0, MATERIAL_ICONS_FONT
    registerMaterialIcons()
    engine = QQmlEngine()
    # The singleton lives next to the QML components of the MaterialIcons module
    engine.addImportPath(os.path.join(os.path.dirname(__file__), "..", "meshroom", "ui", "qml"))
    component = QQmlComponent(engine)
    component.setData(b"import QtQml\nimport MaterialIcons 2.2\n"
                      b"QtObject { property QtObject icons: MaterialIcons }", QUrl())
    root = component.create()
    assert root is not None, component.errorString()
    icons = root.property("icons")
    assert icons.property("fontFamily") == "Material Icons"
    # Every glyph survives the QML compilation, including the ones beyond the Basic Multilingual Plane
    assert icons.property("goat") == MATERIAL_ICONS["goat"]
    assert all(icons.property(name) == glyph for name, glyph in MATERIAL_ICONS.items())
