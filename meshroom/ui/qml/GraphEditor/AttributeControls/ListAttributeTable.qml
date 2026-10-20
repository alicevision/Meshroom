import QtQuick
import QtQuick.Controls

import Controls 1.0
import DataObjects 1.0
import MaterialIcons 2.2

/**
 * ListAttributeTable displays a ListAttribute of GroupAttributes as a table,
 * with one row per element and one column per child attribute.
 * Elements are added from the top-left corner, and removed from their row's header.
 */

MTableView {
    id: root

    required property var attribute
    property bool editable: true

    model: ObjectTableModel {
        id: tableModel
        source: root.attribute.value
    }
    // Editors commit their value when destroyed, which must not happen once reused for another attribute
    reuseItems: false

    delegate: Rectangle {
        id: cell
        required property var object
        readonly property bool isCheckBox: object.type === "BoolParam"
        implicitWidth: valueEditor.implicitWidth + 4
        implicitHeight: valueEditor.implicitHeight + 2
        color: palette.window
        border.color: palette.mid
        clip: true

        AttributeValueEditor {
            id: valueEditor
            anchors.fill: cell.isCheckBox ? undefined : parent
            anchors.centerIn: cell.isCheckBox ? parent : undefined
            anchors.margins: 1
            attribute: cell.object
            editable: root.editable
            // Nested containers can't be edited in a table: only summarize them
            sourceComponent: ["ListAttribute", "GroupAttribute", "AnySet"].includes(cell.object.type) ? containerComponent : valueComponent
        }

        Component {
            id: containerComponent
            Label {
                text: cell.object.value.count + (cell.object.type === "ListAttribute" ? " elements" : " attributes")
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                padding: 4
                enabled: false
            }
        }
    }

    component IconButton: ToolButton {
        font.family: MaterialIcons.fontFamily
        font.pointSize: 11
        padding: 2
        enabled: root.editable
        ToolTip.visible: hovered
    }

    rowHeaderDelegate: IconButton {
        required property int row
        text: MaterialIcons.remove_circle_outline
        ToolTip.text: "Remove Element"
        onClicked: _currentScene.removeAttribute(tableModel.rowObject(row))
    }

    cornerDelegate: IconButton {
        text: MaterialIcons.add_circle_outline
        ToolTip.text: "Add Element"
        onClicked: _currentScene.appendAttribute(root.attribute, undefined)
    }
}
