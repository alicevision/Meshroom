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
        isShape: true
        isAttribute: false
    }

    // Perhaps add an expandable list for current observations later
}
