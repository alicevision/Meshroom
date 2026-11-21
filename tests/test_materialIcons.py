import importlib.util
import os
import re
import subprocess
import sys

import pytest

from meshroom.ui.components.materialIconsData import MATERIAL_ICONS

GENERATOR = os.path.join(os.path.dirname(__file__), "..", "meshroom", "ui", "qml", "MaterialIcons",
                         "generate_material_icons.py")


def test_material_icons_names_are_qml_identifiers():
    for name in MATERIAL_ICONS:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name), name
    # Names clashing with JavaScript keywords or numeric literals are renamed by the generator
    for name in ("delete", "class", "try", "3d_rotation", "123"):
        assert name not in MATERIAL_ICONS
    for name in ("delete_", "class_", "try_", "_3d_rotation", "_123"):
        assert name in MATERIAL_ICONS


def test_material_icons_glyphs():
    assert all(len(glyph) == 1 for glyph in MATERIAL_ICONS.values())
    assert MATERIAL_ICONS["camera"] == ""
    # Codepoints beyond the Basic Multilingual Plane are kept whole
    assert MATERIAL_ICONS["goat"] == "\U0010fffd"


def test_generator_writes_the_icons_dictionary(tmp_path):
    codepoints = tmp_path / "codepoints"
    codepoints.write_text("camera e3af\ndelete e872\n3d_rotation e84d\ncamera e3b0\ngoat 10fffd\n")
    output = tmp_path / "icons.py"
    subprocess.run([sys.executable, GENERATOR, str(codepoints), "--output", str(output)], check=True)

    spec = importlib.util.spec_from_file_location("icons", output)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.MATERIAL_ICONS == {
        "camera": "",
        "delete_": "",
        "_3d_rotation": "",
        "camera2": "",
        "goat": "\U0010fffd",
    }


def test_create_material_icons_exposes_every_icon():
    # Building the map loads the icon font, which needs PySide6.QtGui (and libEGL)
    pytest.importorskip("PySide6.QtGui", exc_type=ImportError)
    from PySide6.QtCore import QObject
    from PySide6.QtGui import QGuiApplication
    from meshroom.ui.components.materialIcons import createMaterialIcons

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    owner = QObject()
    icons = createMaterialIcons(owner)
    assert icons.value("fontFamily") == "Material Icons"
    assert icons.value("camera") == MATERIAL_ICONS["camera"]
    assert all(icons.value(name) == glyph for name, glyph in MATERIAL_ICONS.items())
    assert app is not None
