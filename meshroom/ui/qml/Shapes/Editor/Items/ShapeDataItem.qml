import QtQuick
import QtQuick.Controls

import "Utils" as ItemUtils

/**
* ShapeDataItem
*
* @biref ShapeData component for the ShapeEditor.
* @param shapeData - the given ShapeData model
* @param isNeasted - whether the item is neasted
*/
Column {
    id: shapeDataItem
    width: parent.width
    spacing: 0

    // Properties
    property var shapeData
    property alias isNeasted: itemHeader.isNeasted

    // Item Header
    ItemUtils.ItemHeader {
        id: itemHeader
        model: shapeData
        hasShapeObservation: shapeData.hasObservation(_reconstruction.selectedViewId)
        isShape: true
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
            implicitHeight: 20 

            //Shape data observation
        }
    }
}
