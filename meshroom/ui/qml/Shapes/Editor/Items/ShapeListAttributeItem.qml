import QtQuick
import QtQuick.Controls

import "Utils" as ItemUtils

/**
* ShapeListAttributeItem
*
* @biref ShapeListAttribute component for the ShapeEditor.
* @param shapeListAttribute - the given ShapeListAttribute model
*/
Column {
    id: shapeListAttributeItem
    width: parent.width
    spacing: 0

    // Properties
    property var shapeListAttribute

    // Item Header
    ItemUtils.ItemHeader {
        id: itemHeader
        model: shapeListAttribute
        isShape: false
        isAttribute: true
    }

    // Expandable list
    Loader {
        active: itemHeader.isExpanded
        width: parent.width
        height: active ? (item ? item.implicitHeight || item.height : 0) : 0

        sourceComponent: Pane {
            background: Rectangle { color: "transparent" }
            padding: 0
            implicitWidth: parent.width
            implicitHeight: subList.contentHeight

            ListView {
                id: subList
                anchors.fill: parent
                spacing: 2
                interactive: false
                model: shapeListAttribute.value
                delegate: ShapeAttributeItem {
                    shapeAttribute: object
                    isNeasted: true
                    isLinkChild: shapeListAttribute.isLink
                    width: ListView.view.width
                    height: implicitHeight
                }
            }
        }
    }
}