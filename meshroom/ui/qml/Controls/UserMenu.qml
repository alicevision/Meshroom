import QtQuick
import QtQuick.Controls

Menu {
    id: root
    required property var menuData
    // Nesting level of this menu: 0 for a menu of the menu bar
    property int depth: 0
    // Maximum nesting level of the sub-menus (radio buttons included): deeper ones are displayed disabled, and not built
    property int maxDepth: 2

    title: (menuData != undefined) ? menuData.label : ""

    // HACK: Avoid issues created by the garbage collector
    // Components are created in buildMenu and this means the
    // GC can remove items.
    property var _createdItems: []

    Component {
        id: menuItemComponent
        MenuItem {
            required property var itemData

            text: itemData.label
            icon.source: itemData.icon
            checkable: itemData.objectType === "checkbox"
            checked: itemData.objectType === "checkbox" ? itemData.checked : false

            ToolTip.visible: hovered && itemData.tooltip !== ""
            ToolTip.text: itemData.tooltip

            Shortcut {
                sequence: itemData.shortcut || ""
                enabled: itemData.shortcut !== ""
                context: Qt.ApplicationShortcut
                onActivated: {
                    // Unlike a click, the shortcut does not toggle the checkbox by itself
                    if (checkable)
                        toggle()
                    trigger()
                }
            }

            onTriggered: trigger()

            function trigger() {
                if (itemData.objectType === "checkbox")
                    MeshroomMenuManager.triggerCheckbox(itemData.uid, checked)
                else
                    MeshroomMenuManager.triggerButton(itemData.uid)
            }
        }
    }

    Component {
        id: separatorComponent
        MenuSeparator {}
    }

    // Sub-menu beyond the maximum depth: displayed, but disabled and empty
    Component {
        id: disabledMenuComponent
        Menu {
            id: disabledMenu
            required property var itemData
            title: itemData.label
            enabled: false

            Component.onCompleted: root.setMenuIcon(disabledMenu, itemData.icon)
        }
    }

    Component {
        id: radioMenuComponent
        Menu {
            id: radioMenu
            required property var itemData
            title: itemData.label

            Component.onCompleted: root.setMenuIcon(radioMenu, itemData.icon)

            Repeater {
                model: itemData.items
                RadioButton {
                    required property var modelData
                    text: modelData.label
                    checked: itemData.selectedUid === modelData.name
                    onClicked: MeshroomMenuManager.triggerListEntry(itemData.uid, modelData.name)
                }
            }
        }
    }

    Component.onCompleted: {
        if (menuData !== undefined)
            setMenuIcon(root, menuData.icon)
        // Build the entries later instead of during the creation of this menu: a sub-menu built
        // synchronously is created while its parent is still being created, and Qt aborts beyond
        // a few nested creations ("Component creation is recursing").
        if (menuData !== undefined)
            Qt.callLater(buildMenu)
    }

    // "Menu.icon" may not exist with older Qt versions (Meshroom also runs with Qt 6.5)
    function setMenuIcon(menu, iconSource) {
        if (menu.icon !== undefined && iconSource)
            menu.icon.source = iconSource
    }

    // Close the open sub-menus of this menu (recursively), and clear its current entry so that hovering
    // this entry again starts opening its sub-menu (Qt only opens it when the current entry changes)
    function closeSubMenus() {
        for (let i = 0; i < count; ++i) {
            const subMenu = itemAt(i) ? itemAt(i).subMenu : null
            if (subMenu && subMenu.opened) {
                if (typeof subMenu.closeSubMenus === "function")
                    subMenu.closeSubMenus()
                subMenu.close()
            }
        }
        currentIndex = -1
    }

    // Qt only closes a sub-menu when another entry of the same menu is hovered: when going back to the entry
    // that opened "subMenu", its own sub-menus stay open. Close them, like native menus do.
    function closeNestedMenusOnHover(subMenu) {
        const entry = root.itemAt(root.count - 1)
        entry.hoveredChanged.connect(function() {
            if (entry.hovered && subMenu.opened)
                subMenu.closeSubMenus()
        })
    }

    // Add a disabled entry for a sub-menu that cannot be nested deeper
    function addDisabledMenu(itemData) {
        console.warn("UserMenu: the sub-menu '" + itemData.label + "' of '" + title + "' is disabled: sub-menus cannot be nested more than " + maxDepth + " levels deep.")
        const disabledMenu = disabledMenuComponent.createObject(null, {"itemData": itemData})
        if (disabledMenu) {
            root.addMenu(disabledMenu)
            _createdItems.push(disabledMenu)
        }
    }

    function buildMenu() {
        if (menuData == undefined)
            return

        const items = menuData.objects
        _createdItems = []  // reset

        for (let i = 0; i < items.count; ++i) {
            const itemData = items.at(i)

            switch (itemData.objectType) {
                case "separator": {
                    const sep = separatorComponent.createObject(null)
                    if (sep) {
                        root.addItem(sep)
                        _createdItems.push(sep)
                    }
                    break
                }
                case "menu": {
                    if (depth >= maxDepth) {
                        addDisabledMenu(itemData)
                        break
                    }
                    const subMenuComponent = Qt.createComponent(Qt.resolvedUrl("UserMenu.qml"))
                    if (subMenuComponent.status !== Component.Ready) {
                        console.error("UserMenu: cannot create the sub-menu '" + itemData.label + "': " + subMenuComponent.errorString())
                        break
                    }
                    const subMenu = subMenuComponent.createObject(null, {"menuData": itemData.submenu, "depth": depth + 1, "maxDepth": maxDepth})
                    if (subMenu) {
                        root.addMenu(subMenu)
                        closeNestedMenusOnHover(subMenu)
                        _createdItems.push(subMenu)
                    }
                    break
                }
                case "radiobutton": {
                    if (depth >= maxDepth) {
                        addDisabledMenu(itemData)
                        break
                    }
                    const groupMenu = radioMenuComponent.createObject(null, {"itemData": itemData})
                    if (groupMenu) {
                        root.addMenu(groupMenu)
                        _createdItems.push(groupMenu)
                    }
                    break
                }
                default: {
                    const item = menuItemComponent.createObject(null, {"itemData": itemData})
                    if (item) {
                        root.addItem(item)
                        _createdItems.push(item)
                    }
                    break
                }
            }
        }
    }
}
