import QtQuick
import QtQuick.Shapes

/**
* BaseShape
*
* @biref Shape base component
* @param properties - the given shape style properties
* @param observation - the given shape information for the current view id
*/
Shape {
    id: baseRoot

    // shape model index
    property int modelIndex: -1

    // shape properties
    property var properties: ({})

    // shape observation
    property var observation: ({})

    // shape is editable
    property bool isEditable: false

    // default stroke color of the shape
    readonly property color defaultStrokeColor: "#ffffffff"

    // default stroke width of the shape
    readonly property int defaultStrokeWidth: 2
}