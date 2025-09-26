import QtQuick
import "Layers" as ShapeViewerLayers

/**
* ShapeViewerLayer
*
* @biref Load the corresponding shape layer.
* @param type - the given shape type
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the container scale ratio (scroll zoom)
*/
Loader {
    id: layerLoader

    // Properties
    property string type
    property string name
    property var properties
    property var observation
    property bool editable: false
    property real scaleRatio: 1.0

    // Source component
    sourceComponent: {
        if (!properties || !observation)
            return;
        switch (type) {
            case "Point2d":   return pointLayerComponent
            case "Line2d":    return lineLayerComponent
            case "Circle":    return circleLayerComponent
            case "Rectangle": return rectangleLayerComponent
            case "Text":      return textLayerComponent
        }
    }
    
    // PointLayer component
    Component { 
        id: pointLayerComponent
        ShapeViewerLayers.PointLayer {
            name: layerLoader.name
            properties: layerLoader.properties
            observation: layerLoader.observation
            editable: layerLoader.editable
            scaleRatio: layerLoader.scaleRatio
        } 
    }

    // LineLayer component
    Component { 
        id: lineLayerComponent
        ShapeViewerLayers.LineLayer {
            name: layerLoader.name
            properties: layerLoader.properties
            observation: layerLoader.observation
            editable: layerLoader.editable
            scaleRatio: layerLoader.scaleRatio
        } 
    }

    // CircleLayer component
    Component { 
        id: circleLayerComponent
        ShapeViewerLayers.CircleLayer {
            name: layerLoader.name
            properties: layerLoader.properties
            observation: layerLoader.observation
            editable: layerLoader.editable
            scaleRatio: layerLoader.scaleRatio
        }
    }

    // RectangleLayer component
    Component {
        id: rectangleLayerComponent
        ShapeViewerLayers.RectangleLayer {
            name: layerLoader.name
            properties: layerLoader.properties
            observation: layerLoader.observation
            editable: layerLoader.editable
            scaleRatio: layerLoader.scaleRatio
        } 
    }

    // TextLayer component
    Component { 
        id: textLayerComponent
        ShapeViewerLayers.TextLayer {
            name: layerLoader.name
            properties: layerLoader.properties
            observation: layerLoader.observation
            editable: layerLoader.editable
            scaleRatio: layerLoader.scaleRatio
        } 
    }
}
