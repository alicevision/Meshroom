import QtQuick
import QtQuick.Controls

import "Utils" as ItemUtils

/**
* ShapeAttributeItem
*
* @biref ShapeAttribute component for the ShapeEditor.
* @param shapeAttribute - the given ShapeAttribute model
* @param isNeasted - whether the item is neasted
*/
Column {
    id: shapeAttributeItem
    width: parent.width
    spacing: 0

    // Properties
    property var shapeAttribute
    property alias isNeasted: itemHeader.isNeasted
    property alias isLinkChild: itemHeader.isLinkChild
    
    // Item Header
    ItemUtils.ItemHeader {
        id: itemHeader
        model: shapeAttribute
        isShape: true
        isAttribute: true
    }

    // Perhaps add an expandable list for current observations later
}
