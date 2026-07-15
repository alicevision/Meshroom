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
        }
    }

    Component {
        id: radioMenuItemComponent
        MenuItem {
            required property var groupData
            required property var entryData

            text: entryData.label
            checkable: true
            autoExclusive: true
            checked: groupData.selectedUid === entryData.name

            ToolTip.visible: hovered && entryData.tooltip !== ""
            ToolTip.text: entryData.tooltip

            onTriggered: MeshroomMenuManager.triggerRadioEntry(groupData.uid, entryData.name)
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
                    _createdItems.push(sep)
                    root.insertItem(i, sep)
                    break
                }
                case "menu": {
                    const subMenuComponent = Qt.createComponent(Qt.resolvedUrl("UserMenu.qml"))
                    const subMenu = subMenuComponent.createObject(null, {"menuData": itemData.submenu})
                    _createdItems.push(subMenu)
                    root.insertMenu(i, subMenu)
                    break
                }
                case "radioButton": {
                    const groupMenu = radioMenuComponent.createObject(null, {"itemData": itemData})
                    const entries = itemData.items || []
                    for (let j = 0; j < entries.length; ++j) {
                        const entry = radioMenuItemComponent.createObject(null, {
                            "groupData": itemData,
                            "entryData": entries[j]
                        })
                        groupMenu.insertItem(j, entry)
                        _createdItems.push(entry)
                    }
                    root.insertMenu(i, groupMenu)
                    _createdItems.push(groupMenu)
                    break
                }
                default: {
                    const item = menuItemComponent.createObject(null, {"itemData": itemData})
                    _createdItems.push(item)
                    root.insertItem(i, item)
                    break
                }
            }
        }
    }
}