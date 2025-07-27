import QtQuick
import QtQuick.Shapes

/**
* CircleShape
*
* @biref Display a circle with the given properties.
* @param properties - the given shape style properties
* @param observation - the given shape information for the current view id
*/
BaseShape {
    id: circleRoot

    x: circleRoot.observation.centerX - circleRoot.observation.radius
    y: circleRoot.observation.centerY - circleRoot.observation.radius
    width: circleRoot.observation.radius * 2
    height: width

    ShapePath {
        fillColor: circleRoot.properties.fillColor || "transparent"
        strokeColor: circleRoot.properties.strokeColor || circleRoot.properties.color || circleRoot.defaultStrokeColor
        strokeWidth: (circleRoot.properties.strokeWidth || circleRoot.defaultStrokeWidth) * circleRoot.parent.scaleRatio

        PathRectangle {
            x: 0
            y: 0
            width: circleRoot.width
            height: circleRoot.height
            radius: circleRoot.observation.radius // circle shape
        }
    }
}