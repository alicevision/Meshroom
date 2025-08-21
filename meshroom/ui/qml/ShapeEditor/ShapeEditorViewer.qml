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

    // current node selected shape list index
    property int selectedShapeListIndex: -1

    // current node selected shape index
    property int selectedShapeIndex: -1 

    // current node shape lists
    Repeater {
        model: ShapeEditor.nodeShapeLists
        delegate: Repeater {
            id: shapeListRepeater
            model: shapeListModel

            // shape list index
            property int shapeListIndex: modelIndex

            delegate: Loader {
                id: shapeLayerLoader
                
                // determine the source QML file based on the shape type 
                // shape should be visible
                // shape observation should be defined
                source: {
                    if (model.isVisible === false)        return "";
                    if (model.observation === undefined)  return "";
                    if (model.shapeType === "point2d")    return "ShapeLayers/PointLayer.qml";
                    if (model.shapeType === "line")       return "ShapeLayers/LineLayer.qml";
                    if (model.shapeType === "circle")     return "ShapeLayers/CircleLayer.qml";
                    if (model.shapeType === "rectangle")  return "ShapeLayers/RectangleLayer.qml";
                    if (model.shapeType === "text")       return "ShapeLayers/TextLayer.qml";
                    return "";
                }

                onLoaded: {
                    if (shapeLayerLoader.item) {
                        // set properties from the model
                        shapeLayerLoader.item.modelIndex = model.modelIndex;   // set modelIndex
                        shapeLayerLoader.item.properties = model.properties;   // set properties
                        shapeLayerLoader.item.observation = model.observation; // set observation
                        shapeLayerLoader.item.editable = model.isEditable;     // set editable state
                        // set scale ratio
                        shapeLayerLoader.item.scaleRatio = Qt.binding(function() { return root.scaleRatio });   
                        // set selected state
                        shapeLayerLoader.item.selected = Qt.binding(function() { 
                            return shapeListRepeater.shapeListIndex === root.selectedShapeListIndex && model.modelIndex === root.selectedShapeIndex 
                        }); 
                        // connect selection requested signal 
                        item.selectionRequested.connect(() => {
                            root.selectedShapeListIndex = shapeListRepeater.shapeListIndex
                            root.selectedShapeIndex = model.modelIndex
                        })
                    }
                }
            }
        }
    }
}