import QtQuick
import QtQuick.Shapes

/**
* LineShape
*
* @biref Display a line with the given properties.
* @param properties - the given shape style properties
* @param observation - the given shape information for the current view id
*/
BaseShape {
    id: lineRoot

    x: Math.min(lineRoot.observation.x1, lineRoot.observation.x2)
    y: Math.min(lineRoot.observation.y1, lineRoot.observation.y2)
    width: Math.max(lineRoot.observation.x1, lineRoot.observation.x2)
    height: Math.max(lineRoot.observation.y1, lineRoot.observation.y2)

    ShapePath {
        strokeColor: lineRoot.properties.strokeColor || lineRoot.properties.color || lineRoot.defaultStrokeColor
        strokeWidth: (lineRoot.properties.strokeWidth || lineRoot.defaultStrokeWidth) * lineRoot.parent.scaleRatio

        PathMove {
            x: lineRoot.observation.x1 - lineRoot.x 
            y: lineRoot.observation.y1 - lineRoot.y
        }
        PathLine {
            x: lineRoot.observation.x2 - lineRoot.x
            y: lineRoot.observation.y2 - lineRoot.y
        }
    }
}
