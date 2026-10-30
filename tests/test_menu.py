#!/usr/bin/env python
# coding:utf-8

import logging

import pytest

from meshroom.ui import menu as menuModule
from meshroom.ui.menu import Menu, MenuExtension, MenuItem, MenuObject, MeshroomMenuManager, pruneUnsupportedCharacters


def _noop(menu, app, **kwargs):
    pass


@pytest.fixture(autouse=True)
def clearMenuRegistry():
    """ The registry is class-level: reset it around each test. """
    MeshroomMenuManager.clear()
    yield
    MeshroomMenuManager.clear()


def _latinOnly(codePoint):
    """ Stand-in for the font check: only Latin-1 characters can be displayed. """
    return codePoint < 0x100


def test_pruneUnsupportedCharacters():
    assert pruneUnsupportedCharacters("Plain éàü", _latinOnly) == "Plain éàü"
    # The whitespace left by removed characters is collapsed
    assert pruneUnsupportedCharacters("🚀 Launch  中文 now", _latinOnly) == "Launch now"
    # Joiners and variation selectors of removed emoji sequences are removed with them, combining accents are kept
    assert pruneUnsupportedCharacters("Family 👨\u200d👩 ❤\ufe0f", _latinOnly) == "Family"
    assert pruneUnsupportedCharacters("Cafe\u0301", _latinOnly) == "Cafe\u0301"
    # A label without any displayable character is kept as is
    assert pruneUnsupportedCharacters("中文", _latinOnly) == "中文"


def test_pruneWithoutGuiApplication():
    """ Without a GUI application, the displaying font is unknown: the text is kept. """
    assert pruneUnsupportedCharacters("Launch 🚀") == "Launch 🚀"


def test_labelsArePruned(monkeypatch):
    """ Entries display pruned labels, and labels that only differ by pruned characters are duplicates. """
    original = pruneUnsupportedCharacters
    monkeypatch.setattr(menuModule, "pruneUnsupportedCharacters", lambda text, isSupported=None: original(text, _latinOnly))
    menu = Menu("Tools 🛠")
    assert menu.label == "Tools"
    button = menu.addButton("launch", label="🚀 Launch", callback=_noop)
    assert button.label == "Launch"
    with pytest.raises(ValueError, match="labelled"):
        menu.addButton("launch2", label="Launch 🎉", callback=_noop)
    group = menu.addRadioButton("mode", items=[MenuItem("a", label="Fast ⚡"), MenuItem("b", label="Slow")], callback=_noop)
    assert [item.label for item in group.items] == ["Fast", "Slow"]

