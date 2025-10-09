import QtQuick

/**
* BaseLayer
*
* @biref Shape layer base component for displaying and modifying shapes.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
*/
Item {
    id: baseLayer

    // Shape layer fills the parent
    anchors.fill: parent

    // Shape name
    property string name: "unknown"

    // Shape properties
    property var properties: ({})

    // Shape observation
    property var observation: ({})

    // Shape is editable
    property bool editable: false

    // Shape container scale ratio
    property real scaleRatio: 1.0

    // Shape is selected
    property bool selected: ShapeViewerHelper.selectedShapeName === name

    // Shape default color 
    readonly property color defaultColor: "#3366cc"

    // Request selection
    function selectionRequested() {
        ShapeViewerHelper.selectedShapeName = name
    }

    // Helper function to get scaled handle size
    function getScaledHandleSize() {
        return Math.max(0.5, 8.0 * scaleRatio)
    }

    // Helper function to get scaled stroke width
    function getScaledStrokeWidth() {
        return Math.max(0.05, (baseLayer.properties.strokeWidth || 2.0) * baseLayer.scaleRatio)
    }

    // Helper function to get scaled helper stroke width
    function getScaledHelperStrokeWidth() {
        return Math.max(0.05, baseLayer.scaleRatio)
    }

    // Helper function to get scaled font size
    function getScaledFontSize() {
        return Math.max(1.0, (baseLayer.properties.fontSize || 10.0) * baseLayer.scaleRatio)
    }
}