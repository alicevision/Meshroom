import QtQuick

/**
* ShapeEditorViewer
*
* @biref A canvas to display current node shape parameters and shape files.
* @param containerScale - the parent image container scale
*/
Item {
    id: root

    // container scale
    property real containerScale: 1.0

    // container scale ratio
    property real scaleRatio: (1 / root.containerScale)

    // current node shape lists
    Repeater {
        model: ShapeEditor.nodeShapeLists
        delegate: ShapeListRepeater { 
            model: shapeListModel
            scaleRatio: root.scaleRatio
        }
    }
}