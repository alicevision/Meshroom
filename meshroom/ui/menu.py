#!/usr/bin/env python

"""
On top of the Meshroom menus that are set-up in the QML
we can register additional menus that will trigger a callback if we click on the menu entry.

Example :
    def open_settings_ui(menu, app, **kwargs):
        ...

    settings_menu = Menu("Settings")
    settings_menu.addButton("Open Settings", callback=open_settings_ui)
    MeshroomMenuManager.registerMenu(settings_menu)
"""

import logging
import uuid
from enum import Enum
from typing import Optional, Callable

from meshroom.common import BaseObject, Property, Signal, Slot, Variant, ListModel


class MenuCallback:
    """ Override __call__ to react to menu interactions.
    Can also be defined with a lamba or a function.
    """
    def __call__(self, menu, app, **kwargs):
        pass


class MenuObjectType(Enum):
    MENU = "menu"
    SEPARATOR = "separator"
    BUTTON = "button"
    CHECKBOX = "checkbox"
    RADIOBUTTON = "radioButton"


class MenuItem(BaseObject):
    """A simple (name, label) pair, used for radio button entries."""

    def __init__(self, name, label=None, tooltip=None, shortcut=None, parent=None):
        super().__init__(parent)
        self._name = name
        self._label = label or name
        self._tooltip = tooltip or ""
        self._shortcut = shortcut or ""

    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    tooltip = Property(str, lambda self: self._tooltip, constant=True)
    shortcut = Property(str, lambda self: self._shortcut, constant=True)


class MenuObject(BaseObject):
    """
    Item registered as an entry in a menu.
    Can be either: a menu, a separator, a button, a checkbox, a radioButton.
    """

    def __init__(self, parent: "Menu", callback: Optional[MenuCallback],
                 menuObjectType: MenuObjectType, **kwargs):
        if menuObjectType not in MenuObjectType:
            raise ValueError(
                f"Invalid MenuObject type: {menuObjectType} (valid types are " +
                ", ".join(m.name for m in MenuObjectType) + ")"
            )

        super().__init__(parent)

        self._uid: str = uuid.uuid4().hex
        self.parentMenu: "Menu" = parent
        self.callback: Callable = callback
        self.menuObjectType: MenuObjectType = menuObjectType

        # General properties
        self._name: str = kwargs.get("name", "")
        self._label: str = kwargs.get("label", self._name)
        self._icon: str = kwargs.get("icon", "")
        self._tooltip: str = kwargs.get("tooltip", "")
        self._shortcut: str = kwargs.get("shortcut", "")
        self.index: int = kwargs.get("index", -1)

        # Menu
        self._submenu: "Menu" = kwargs.get("submenu", None)
        # Checkbox
        self._checked: bool = kwargs.get("checked", False)
        # Radio Button
        self._items: list = kwargs.get("items") or []
        self._selectedUid: str = kwargs.get("selectedUid", "")

    def _setSubmenu(self, menu: "Menu"):
        self._submenu = menu

    def _setChecked(self, value):
        if self._checked != value:
            self._checked = value
            self.checkedChanged.emit()

    def _setSelectedUid(self, value):
        if self._selectedUid != value:
            self._selectedUid = value
            self.selectedUidChanged.emit()

    def trigger(self, app, **kwargs):
        if self.callback is not None:
            return self.callback(self.parentMenu, app, **kwargs)
        return None

    uid = Property(str, lambda self: self._uid, constant=True)
    objectType = Property(str, lambda self: self.menuObjectType.value, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    icon = Property(str, lambda self: self._icon, constant=True)
    tooltip = Property(str, lambda self: self._tooltip, constant=True)
    shortcut = Property(str, lambda self: self._shortcut, constant=True)
    # type: Menu
    submenu = Property(Variant, lambda self: self._submenu, constant=True)
    # type: Checkbox
    checkedChanged = Signal()
    checked = Property(bool, lambda self: self._checked, _setChecked, notify=checkedChanged)
    # type: RadioButton
    selectedUidChanged = Signal()
    selectedUid = Property(str, lambda self: self._selectedUid, _setSelectedUid, notify=selectedUidChanged)
    items = Property("QVariantList", lambda self: self._items, constant=True)


class Menu(BaseObject):
    """Registerable menu (or submenu)."""

    def __init__(self, name: str, icon: str = None, tooltip: str = None,
                 parent: "Menu" = None, index: int = -1):
        super().__init__(parent)
        self._uid: str = uuid.uuid4().hex
        self._name: str = name
        self._icon: str = icon or ""
        self._tooltip: str = tooltip or ""
        self.parentMenu: "Menu" = parent
        self.index: int = index
        self.menuObject = MenuObject(
            parent=self, callback=None, menuObjectType=MenuObjectType.MENU,
            # and kwargs :
            name=name, label=name, icon=icon, tooltip=tooltip, index=index
        )
        self._objects: ListModel = ListModel(parent=self)
        self._initialized = False

    def __repr__(self):
        return f'<Menu name="{self._name}"|uid={self._uid}|size={len(self._objects)}>'
    
    def _addObject(self, obj: MenuObject):
        self._objects.append(obj)
        self.objectsChanged.emit()

    def addSubmenu(self, name, icon=None, tooltip="", index=-1) -> "Menu":
        submenu = Menu(name, icon=icon, tooltip=tooltip, parent=self, index=index)
        submenu.menuObject._setSubmenu(submenu)
        self._addObject(submenu.menuObject)
        return submenu

    def addSeparator(self, index=-1):
        obj = MenuObject(self, None, MenuObjectType.SEPARATOR, index=index)
        self._addObject(obj)
        return obj

    def addButton(self, name, callback: MenuCallback, label=None,
                  icon=None, tooltip="", index=-1, shortcut=None):
        obj = MenuObject(self, callback, MenuObjectType.BUTTON,
                         name=name, label=label or name, icon=icon,
                         tooltip=tooltip, index=index, shortcut=shortcut)
        self._addObject(obj)
        return obj

    def addCheckbox(self, name, callback: MenuCallback, label=None, icon=None,
                     tooltip="", index=-1, shortcut=None, checked=False):
        obj = MenuObject(self, callback, MenuObjectType.CHECKBOX,
                          name=name, label=label or name, icon=icon,
                          tooltip=tooltip, index=index, shortcut=shortcut,
                          checked=checked)
        self._addObject(obj)
        return obj

    def addRadioButton(self, name, items: list[MenuItem], callback: MenuCallback,
                        label=None, icon=None, tooltip="", index=-1):
        """
        Acts as a sub-menu: each entry in `items` becomes a selectable radio entry.
        """
        for item in items:
            item.setParent(self)

        group = MenuObject(self, callback, MenuObjectType.RADIOBUTTON,
                           name=name, label=label or name, icon=icon,
                           tooltip=tooltip, index=index, items=items)
        if items:
            group.selectedUid = items[0].name
        self._addObject(group)
        return group

    def onCreated(self):
        """Override to react once the menu has been registered (e.g. add entries)."""
        pass

    objectsChanged = Signal()
    uid = Property(str, lambda self: self._uid, constant=True)
    label = Property(str, lambda self: self._name, constant=True)
    icon = Property(str, lambda self: self._icon, constant=True)
    tooltip = Property(str, lambda self: self._tooltip, constant=True)
    objects = Property(Variant, lambda self: self._objects, notify=objectsChanged)


class MenuExtension:
    """Object used to extend another existing menu.
    You can use a MenuExtension and then use the `registerMenuExtension`
    method of `MeshroomMenuManager` to add entries to a top-level menu.
    """

    parent: str = None

    def __init__(self):
        self.parentMenu: Optional[Menu] = None

    def _bind(self, parentMenu: Menu):
        self.parentMenu = parentMenu
        self.register()

    def register(self):
        """ Populate the parent menu with new items. """
        raise NotImplementedError(
            f"{self.__class__.__name__} needs to override the 'register' method."
        )

    def __getattr__(self, name):
        if not name.startswith("add"):
            raise AttributeError(
                f"attribute {name!r} should start with 'add'"
            )
        if hasattr(self.parentMenu, name):
            return getattr(self.parentMenu, name)
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )


class MeshroomMenuManager(BaseObject):
    """
    Registry of all user menus and their objects.
    
    - _menus are the list of menus that are registered
    - _objects is a dict to retrieve objects from their UID. The interface has access to the object
      UID and therefore when we click on it, we retrieve the object throught the UID and we can
      call the callback
    - _menuModel is a ListModel built upon the _menus so that we can instanciate the QML objects
    """

    _menus: list[Menu] = []
    _objects: dict[str, MenuObject] = {}
    # _menusByName contains only top-level menus
    _menusByName: dict[str, Menu] = {}
    # _menuExtensions can be attached to top-level menus
    _menuExtensions: dict[str, list["MenuExtension"]] = {}
    
    LIST_OBJ_TYPES = [
        MenuObjectType.RADIOBUTTON.value
    ]

    def __init__(self, parent=None):
        self._indexMenuExtensions()
        super().__init__(parent)
        self._menuModel: ListModel = ListModel(parent=self)
        self._menuModel.setObjectList(self._menus)
        logging.info(f"Initialize MeshroomMenuManager with {len(self._menus)} menus.")
        for menu in self._menus:
            if menu._initialized:
                continue
            logging.info(f"Initialize User Menu: {menu}")
            menu.onCreated()
            menu._initialized = True

    @classmethod  
    def clear(cls):  
        """Clear all registered menus and objects. Useful for testing and resetting state."""  
        cls._menus.clear()
        cls._objects.clear()
        cls._menusByName.clear()
        cls._menuExtensions.clear()

    @property
    def app(self):
        return self.parent()

    @classmethod
    def _indexMenu(cls, menu: Menu):
        """ Build the _objects map
        """
        cls._objects[menu.menuObject.uid] = menu.menuObject
        for obj in menu._objects:  # iterate CoreListModel/QObjectListModel directly
            cls._objects[obj.uid] = obj
            if obj.objectType == MenuObjectType.MENU.value:
                cls._indexMenu(obj.submenu)

    @classmethod
    def _indexMenuExtensions(cls):
        for parentMenuName, extensions in cls._menuExtensions.items():
            parentMenu = cls._menusByName.get(parentMenuName)
            if parentMenu is None:
                logging.error(
                    f"Parent menu '{parentMenuName}' is not registered: "
                    f"cannot add {len(extensions)} extension(s)"
                    f" ({', '.join(e.__class__.__name__ for e in extensions)})."
                )
                continue
            for extension in extensions:
                extension._bind(parentMenu)
                # re-index parent menus
                cls._indexMenu(parentMenu)

    @classmethod
    def registerMenu(cls, menu: Menu):
        cls._menus.append(menu)
        cls._menusByName[menu._name] = menu
        cls._indexMenu(menu)

    @classmethod
    def registerMenuExtension(cls, extension: MenuExtension):
        """Register a menu to append to another menu.
        It's first added in the _menuExtensions dict and then indexed during the initialization
        of MeshroomMenuManager.
        """
        cls._menuExtensions.setdefault(extension.parent, []).append(extension)

    def getMenus(self) -> ListModel:
        return self._menuModel

    def getObject(self, uid: str) -> Optional[MenuObject]:
        return self._objects.get(uid)

    def trigger(self, uid: str, **kwargs):
        obj = self.getObject(uid)
        if obj is None:
            return None
        return obj.trigger(self.app, **kwargs)

    @Slot(str)
    def triggerButton(self, uid: str):
        self.trigger(uid)

    @Slot(str, bool)
    def triggerCheckbox(self, uid: str, checked: bool):
        obj = self.getObject(uid)
        if obj is None:
            return
        obj.checked = checked
        self.trigger(uid, enabled=checked)

    @Slot(str, str)
    def triggerListEntry(self, groupUid: str, entryName: str):
        obj = self.getObject(groupUid)
        if obj is None or obj.menuObjectType in self.LIST_OBJ_TYPES:
            return
        item = next((i for i in obj.items if i.name == entryName), None)
        if item is None:
            return
        obj.selectedUid = entryName
        self.trigger(groupUid, selected=item)

    menusChanged = Signal()
    menus = Property(BaseObject, getMenus, notify=menusChanged)
