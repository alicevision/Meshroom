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


def test_allMenuTypes():
    assert set(MenuObject.allMenuTypes()) == {"menu", "separator", "button", "checkbox", "radiobutton"}


def test_nonCallableCallbackIsRejected():
    """ Passing the result of a call instead of the function raises a clear error. """
    menu = Menu("Test")
    with pytest.raises(TypeError, match="Pass the function itself"):
        # e.g. "callback=subprocess.run(...)" gives a CompletedProcess
        menu.addButton("run", callback=object())
    with pytest.raises(TypeError):
        menu.addCheckbox("toggle", callback="notCallable")
    assert len(menu._objects) == 0


def test_duplicateEntriesAreRejected():
    menu = Menu("Test")
    menu.addButton("a", callback=_noop, label="A")
    with pytest.raises(ValueError, match="named 'a'"):
        menu.addCheckbox("a", callback=_noop, label="Other")
    with pytest.raises(ValueError, match="labelled 'A'"):
        menu.addButton("b", callback=_noop, label="A")
    with pytest.raises(ValueError):
        menu.addSubmenu("a")
    # Separators have no name and can be repeated
    menu.addSeparator()
    menu.addSeparator()
    assert len(menu._objects) == 3


def test_duplicateRadioItemsAreRejected():
    menu = Menu("Test")
    with pytest.raises(ValueError, match="same name: x"):
        menu.addRadioButton("choice", items=[MenuItem("x", label="X"), MenuItem("x", label="Y")], callback=_noop)
    with pytest.raises(ValueError, match="same label: X"):
        menu.addRadioButton("choice", items=[MenuItem("x", label="X"), MenuItem("y", label="X")], callback=_noop)
    group = menu.addRadioButton("choice", items=[MenuItem("x"), MenuItem("y")], callback=_noop)
    assert group.selectedUid == "x"


def test_entryIndex():
    """ Entries are inserted at their index, or appended when it is not a valid position. """
    menu = Menu("Test")
    menu.addButton("a", callback=_noop)
    menu.addButton("b", callback=_noop)
    menu.addButton("c", callback=_noop, index=0)
    menu.addButton("d", callback=_noop, index=1)
    menu.addButton("e", callback=_noop, index=42)
    assert [obj._name for obj in menu._objects] == ["c", "d", "a", "b", "e"]


def test_registerMenus():
    """ Several menus can be registered, and a menu name can only be registered once. """
    first, second = Menu("First"), Menu("Second")
    MeshroomMenuManager.registerMenu(first)
    MeshroomMenuManager.registerMenu(second)
    MeshroomMenuManager.registerMenu(Menu("First"))
    MeshroomMenuManager.registerMenu(Menu("Zeroth", index=0))
    assert [menu._name for menu in MeshroomMenuManager._menus] == ["Zeroth", "First", "Second"]
    assert MeshroomMenuManager._menusByName["First"] is first


def test_triggerCallbacks():
    calls = []
    menu = Menu("Test")
    button = menu.addButton("button", callback=lambda menu, app, **kwargs: calls.append(("button", kwargs)))
    checkbox = menu.addCheckbox("checkbox", callback=lambda menu, app, **kwargs: calls.append(("checkbox", kwargs)))
    radio = menu.addRadioButton("radio", items=[MenuItem("x"), MenuItem("y")],
                                callback=lambda menu, app, **kwargs: calls.append(("radio", kwargs["selected"].name)))
    MeshroomMenuManager.registerMenu(menu)
    manager = MeshroomMenuManager()

    manager.triggerButton(button.uid)
    manager.triggerCheckbox(checkbox.uid, True)
    manager.triggerListEntry(radio.uid, "y")
    manager.triggerListEntry(radio.uid, "unknown")

    assert calls == [("button", {}), ("checkbox", {"enabled": True}), ("radio", "y")]
    assert checkbox.checked
    assert radio.selectedUid == "y"


def test_entriesAddedAfterRegistrationAreTriggered():
    """ Entries added in "onCreated" or after "registerMenu" are found when triggered. """
    calls = []

    class LateMenu(Menu):
        def onCreated(self):
            self.lateButton = self.addButton("fromOnCreated", callback=lambda menu, app, **kwargs: calls.append("onCreated"))

    menu = LateMenu("Late")
    MeshroomMenuManager.registerMenu(menu)
    afterRegister = menu.addButton("afterRegister", callback=lambda menu, app, **kwargs: calls.append("afterRegister"))
    manager = MeshroomMenuManager()

    manager.triggerButton(menu.lateButton.uid)
    manager.triggerButton(afterRegister.uid)
    assert calls == ["onCreated", "afterRegister"]


def test_failingUserCodeDoesNotBreakManager(caplog):
    """ Errors raised by user code while the manager initializes are logged instead of propagated. """
    class FailingMenu(Menu):
        def onCreated(self):
            raise RuntimeError("onCreated failure")

    class FailingExtension(MenuExtension):
        parent = "Target"

        def register(self):
            raise RuntimeError("register failure")

    MeshroomMenuManager.registerMenu(FailingMenu("Failing"))
    MeshroomMenuManager.registerMenu(Menu("Target"))
    MeshroomMenuManager.registerMenuExtension(FailingExtension())

    with caplog.at_level(logging.ERROR):
        manager = MeshroomMenuManager()
    assert "onCreated failure" in caplog.text
    assert "register failure" in caplog.text
    assert len(manager.menus) == 2


def test_extensionIsBoundOnce():
    """ Instantiating the manager several times does not add the extension's entries again. """
    class Extension(MenuExtension):
        parent = "Target"

        def register(self):
            self.addButton("extra", callback=_noop)

    target = Menu("Target")
    MeshroomMenuManager.registerMenu(target)
    MeshroomMenuManager.registerMenuExtension(Extension())

    # Keep both alive: the registered menus are owned by the manager's model
    managers = [MeshroomMenuManager(), MeshroomMenuManager()]
    assert len(managers[1].menus) == 1
    assert [obj._name for obj in target._objects] == ["extra"]
