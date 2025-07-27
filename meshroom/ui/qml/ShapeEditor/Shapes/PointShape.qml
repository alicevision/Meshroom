import QtQuick
import QtQuick.Shapes

/**
* PointShape
*
* @biref Display a point with the given properties.
* @param properties - the given point style properties
* @param observation - the given point information for the current view id
*/
BaseShape {
    id: pointRoot

    property real size: Math.max(1, (pointRoot.properties.size || 10) * pointRoot.parent.scaleRatio)

    x: pointRoot.observation.x - (size * 0.5)
    y: pointRoot.observation.y - (size * 0.5)
    width: size
    height: size

    ShapePath {
        fillColor: pointRoot.properties.fillColor || pointRoot.properties.color || pointRoot.defaultStrokeColor
        strokeColor: pointRoot.properties.strokeColor || pointRoot.defaultStrokeColor
        strokeWidth: (pointRoot.properties.strokeWidth || 0)  * pointRoot.parent.scaleRatio

        PathRectangle {
            x: 0
            y: 0
            width: pointRoot.width
            height: pointRoot.height
        }
    }
}