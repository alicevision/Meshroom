import QtQuick

/**
* TextLayer
*
* @biref Allows to display a text.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
* @see BaseLayer.qml
*/
BaseLayer {
    id: textLayer

    Text {
        width: ShapeViewerHelper.containerWidth - textLayer.observation.center.x
        height: ShapeViewerHelper.containerHeight - textLayer.observation.center.y

        x: textLayer.observation.center.x
        y: textLayer.observation.center.y
        text: textLayer.observation.content || "Undefined"
        color: textLayer.properties.color || textLayer.defaultColor
        wrapMode: Text.Wrap
        font.family: textLayer.properties.fontFamily || "Arial"
        font.pixelSize: getScaledFontSize()
    }
}