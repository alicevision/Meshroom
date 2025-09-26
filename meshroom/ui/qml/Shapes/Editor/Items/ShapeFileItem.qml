import QtQuick
import QtQuick.Controls

import "Utils" as ItemUtils

/**
* ShapeFileItem
*
* @biref ShapeFile component for the ShapeEditor.
* @param shapeFile - the given ShapeFile model
*/
Column {
    id: shapeFileItem
    width: parent.width
    spacing: 0

    // Properties
    property var shapeFile

    // Item Header
    ItemUtils.ItemHeader {
        id: itemHeader
        model: shapeFile
        isShape: false
        isAttribute: false
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
                model: shapeFile.shapes
                delegate: ShapeDataItem {
                    shapeData: object
                    isNeasted: true
                    width: ListView.view.width
                    height: implicitHeight
                }
            }
        }
    }
}