import QtQuick

/**
* ShapeListRepeater
*
* @biref Repeater to create shape items based on the given ShapeList model.
* @param model - the given ShapeList model
* @param scaleRatio - container scale ratio (scroll zoom)
*/
Repeater {
    id: shapeListRepeater
    
    // container scale ratio
    property real scaleRatio: 1.0

    delegate: Loader {
        id: shapeLoader

        // container scale ratio
        property real scaleRatio: shapeListRepeater.scaleRatio
        
        // determine the source QML file based on the shape type 
        // shape should be visible
        // shape observation should be defined
        source: {
            if (model.isVisible === false)        return "";
            if (model.observation === undefined)  return "";
            if (model.shapeType === "point2d")    return "Shapes/PointShape.qml";
            if (model.shapeType === "line")       return "Shapes/LineShape.qml";
            if (model.shapeType === "circle")     return "Shapes/CircleShape.qml";
            if (model.shapeType === "rectangle")  return "Shapes/RectangleShape.qml";
            if (model.shapeType === "text")       return "Shapes/TextShape.qml";
            return "";
        }

        onLoaded: {
            if (shapeLoader.item) {
                shapeLoader.item.modelIndex = model.modelIndex;   // set modelIndex for the shape
                shapeLoader.item.properties = model.properties;   // set properties for the shape
                shapeLoader.item.observation = model.observation; // set observation for the shape
                shapeLoader.item.isEditable = model.isEditable;   // set editable state for the shape
            }
        }
    }
}