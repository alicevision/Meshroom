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


    function hasCurrentObservation() {
        return shapeAttribute ? shapeAttribute.hasObservation(_reconstruction ? _reconstruction.selectedViewId : "-1") : false
    }

    // Reload hasObservation property
    // When shape attribute observations changed (signal)
    Connections {
        target: shapeAttribute
        function onObservationsChanged() { itemHeader.hasShapeObservation = hasCurrentObservation() }
    }
    // When reconstruction view id changed (signal)
    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() { itemHeader.hasShapeObservation = hasCurrentObservation() }
    }
    
    // Item Header
    ItemUtils.ItemHeader {
        id: itemHeader
        model: shapeAttribute
        hasShapeObservation: hasCurrentObservation()
        isShape: true
        isAttribute: true
    }

    // Perhaps add an expandable list for current observations later
}
