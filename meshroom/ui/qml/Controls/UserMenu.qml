import QtQuick
import QtQuick.Controls

Menu {
    id: root
    required property var menuData

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
            icon.source: itemData.icon !== "" ? itemData.icon : undefined
            checkable: itemData.objectType === "checkbox"
            checked: itemData.objectType === "checkbox" ? itemData.checked : false

            ToolTip.visible: hovered && itemData.tooltip !== ""
            ToolTip.text: itemData.tooltip

            Shortcut {
                sequence: itemData.shortcut || ""
                enabled: itemData.shortcut !== ""
                context: Qt.ApplicationShortcut
                onActivated: trigger()
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

    Component {
        id: radioMenuComponent
        Menu {
            required property var itemData
            title: itemData.label

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
            buildMenu()
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
                    root.insertItem(i, sep)
                    _createdItems.push(sep)
                    break
                }
                case "menu": {
                    const subMenuComponent = Qt.createComponent(Qt.resolvedUrl("UserMenu.qml"))
                    const subMenu = subMenuComponent.createObject(null, {"menuData": itemData.submenu})
                    root.insertMenu(i, subMenu)
                    _createdItems.push(subMenu)
                    break
                }
                case "radiobutton": {
                    const groupMenu = radioMenuComponent.createObject(null, {"itemData": itemData})
                    root.insertMenu(i, groupMenu)
                    _createdItems.push(groupMenu)
                    break
                }
                default: {
                    const item = menuItemComponent.createObject(null, {"itemData": itemData})
                    root.insertItem(i, item)
                    _createdItems.push(item)
                    break
                }
            }
        }
    }
}