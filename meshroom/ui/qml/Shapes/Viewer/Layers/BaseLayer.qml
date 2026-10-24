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
    property bool selected: ShapeViewerHelper.selectedShapeNames.indexOf(name) >= 0

    // Shape default color
    readonly property color defaultColor: "#3366cc"

    // Item moved by the shape move drags (set by each layer)
    property Item moveTarget: null

    // Shape is part of a multiple selection: moving it moves all the selected shapes
    readonly property bool inMultipleSelection: selected && ShapeViewerHelper.selectedShapeNames.length > 1

    // Follow the move of another selected shape
    readonly property bool followsSelectionMove: selected && ShapeViewerHelper.selectionMoveSource !== ""
                                                 && ShapeViewerHelper.selectionMoveSource !== name
    transform: Translate {
        x: baseLayer.followsSelectionMove ? ShapeViewerHelper.selectionMoveOffset.x : 0
        y: baseLayer.followsSelectionMove ? ShapeViewerHelper.selectionMoveOffset.y : 0
    }

    // Share the drag offset with the other selected shapes
    Connections {
        target: baseLayer.moveTarget
        enabled: baseLayer.inMultipleSelection
        function onXChanged() { ShapeViewerHelper.setSelectionMoveOffset(baseLayer.name, baseLayer.moveTarget.x, baseLayer.moveTarget.y) }
        function onYChanged() { ShapeViewerHelper.setSelectionMoveOffset(baseLayer.name, baseLayer.moveTarget.x, baseLayer.moveTarget.y) }
    }

    // Commit the move of the moveTarget for all the selected shapes in a multiple selection
    // Returns false if the shape is selected alone, to let the layer commit its own move
    function commitSelectionMove() {
        if (!inMultipleSelection)
            return false
        ShapeViewerHelper.moveSelectedShapes(moveTarget.x, moveTarget.y)
        return true
    }

    // Request selection: Ctrl toggles the shape in the selection, otherwise select it alone
    // Take the focus so that the 2d Viewer receives key events (e.g. Delete)
    function selectionRequested(modifiers) {
        if (modifiers & Qt.ControlModifier)
            ShapeViewerHelper.toggleShapeSelection(name)
        else
            ShapeViewerHelper.selectedShapeNames = [name]
        baseLayer.forceActiveFocus()
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