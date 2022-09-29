import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import MaterialIcons 2.2
import Utils 1.0

/**
 * A component to display and edit the attributes of a Node.
 */

ListView {
    id: root
    property bool readOnly: false
    property int labelWidth: 180

    signal upgradeRequest()
    signal attributeDoubleClicked(var mouse, var attribute)

    implicitHeight: contentHeight

    spacing: 2
    clip: true
    ScrollBar.vertical: ScrollBar { id: scrollBar }

    delegate: Loader {
        active: object.enabled && (!object.desc.advanced || GraphEditorSettings.showAdvancedAttributes)
        visible: active

        sourceComponent: AttributeItemDelegate {
            width: root.width - scrollBar.width
            readOnly: root.readOnly
            labelWidth: root.labelWidth
            attribute: object
            onDoubleClicked: function (mouse) { root.attributeDoubleClicked(mouse, attr) }
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

