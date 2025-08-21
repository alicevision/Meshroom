import QtQuick

/**
* ShapeListRepeater
*
* @biref Repeater to create shape items based on the given ShapeList model.
* @param model - the given ShapeList model
* @param scaleRatio - container scale ratio (scroll zoom)
*/
Repeater {
    id: root
    
    // container scale ratio
    property real scaleRatio: 1.0

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
            }
        }
    }
}