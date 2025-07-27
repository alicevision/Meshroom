import QtQuick
import QtQuick.Shapes

/**
* RectangleShape
*
* @biref Display a rectangle with the given properties.
* @param properties - the given shape style properties
* @param observation - the given shape information for the current view id
*/
BaseShape {
    id: rectangleRoot

    x: rectangleRoot.observation.centerX - (rectangleRoot.observation.width * 0.5)
    y: rectangleRoot.observation.centerY - (rectangleRoot.observation.height * 0.5)
    width: rectangleRoot.observation.width
    height: rectangleRoot.observation.height

    ShapePath {
        fillColor: rectangleRoot.properties.fillColor || "transparent"
        strokeColor: rectangleRoot.properties.strokeColor || rectangleRoot.properties.color || rectangleRoot.defaultStrokeColor
        strokeWidth: (rectangleRoot.properties.strokeWidth || rectangleRoot.defaultStrokeWidth) * rectangleRoot.parent.scaleRatio

        PathRectangle {
            x: 0
            y: 0
            width: rectangleRoot.width
            height: rectangleRoot.height
        }
    }
}