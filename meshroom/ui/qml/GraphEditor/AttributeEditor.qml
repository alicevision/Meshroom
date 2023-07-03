import QtQuick 2.15
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.15
import MaterialIcons 2.2
import Utils 1.0

/**
 * A component to display and edit the attributes of a Node.
 */

ListView {
    id: root
    property bool readOnly: false
    property int labelWidth: 180
    property bool objectsHideable: true
    property string filterText: ""

    signal upgradeRequest()
    signal attributeDoubleClicked(var mouse, var attribute)

    implicitHeight: contentHeight

    spacing: 2
    clip: true
    ScrollBar.vertical: ScrollBar { id: scrollBar }

    delegate: Loader {
        active: object.enabled && (
            !objectsHideable
            || ((!object.desc.advanced || GraphEditorSettings.showAdvancedAttributes)
            && (object.isDefault && GraphEditorSettings.showDefaultAttributes || !object.isDefault && GraphEditorSettings.showModifiedAttributes)
            && (object.isOutput && GraphEditorSettings.showOutputAttributes || !object.isOutput && GraphEditorSettings.showInputAttributes)
            && (object.isLinkNested && GraphEditorSettings.showLinkAttributes || !object.isLink && GraphEditorSettings.showNotLinkAttributes))
        ) && object.matchText(filterText)
        visible: active

        sourceComponent: AttributeItemDelegate {
            width: root.width - scrollBar.width
            readOnly: root.readOnly
            labelWidth: root.labelWidth
            filterText: root.filterText
            objectsHideable: root.objectsHideable
            attribute: object
            onDoubleClicked: root.attributeDoubleClicked(mouse, attr)
        }

        onActiveChanged: height = active ? item.implicitHeight : -spacing

        Connections {
            target: item
            function onImplicitHeightChanged() {
                // Handles cases where an attribute is created and its height is then updated as it is filled
                height = item.implicitHeight
            }
        }
    }

    // Helper MouseArea to lose edit/activeFocus
    // when clicking on the background
    MouseArea {
        anchors.fill: parent
        onClicked: root.forceActiveFocus()
        z: -1
    }
}

