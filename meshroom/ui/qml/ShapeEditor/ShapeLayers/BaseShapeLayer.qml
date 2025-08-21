import QtQuick

/**
* BaseShapeLayer
*
* @biref Shape layer base component for displaying and modifying shapes.
* @param modelIndex - the given shape index
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param selected - the shape is selected
* @param scaleRatio - the shape container scale ratio (scroll zoom)
*/
Item {
    id: root

    // shape layer fills the parent
    anchors.fill: parent

    // signal to request selection
    signal selectionRequested()

    // shape model index
    property int modelIndex: -1

    // shape properties
    property var properties: ({})

    // shape observation
    property var observation: ({})

    // shape is editable
    property bool editable: false

    // shape is selected
    property bool selected: false

    // shape container scale ratio
    property real scaleRatio: 1.0

    // shape default color 
    readonly property color defaultColor: "#3366cc"

    // helper function to get scaled point size
    function getScaledPointSize() {
        return Math.max(0.5, (root.properties.size || 10.0) * root.scaleRatio)
    }

    // helper function to get scaled handle size
    function getScaledHandleSize() {
        return Math.max(1.0, 8.0 * root.scaleRatio)
    }

    // helper function to get scaled stroke width
    function getScaledStrokeWidth() {
        return Math.max(0.05, (root.properties.strokeWidth || 2.0) * root.scaleRatio)
    }

    // helper function to get scaled helper stroke width
    function getScaledHelperStrokeWidth() {
        return Math.max(0.05, root.scaleRatio)
    }

    // helper function to get scaled font size
    function getScaledFontSize() {
        return Math.max(4.0, (root.properties.fontSize || 10.0) * root.scaleRatio)
    }
}