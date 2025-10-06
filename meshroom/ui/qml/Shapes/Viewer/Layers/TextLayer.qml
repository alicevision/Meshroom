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
        x: textLayer.observation.center.x - implicitWidth * 0.5   // Center text horizontally
        y: textLayer.observation.center.y - implicitHeight * 0.5  // Center text vertically
        text: textLayer.observation.content || "Undefined"
        color: textLayer.properties.color || textLayer.defaultColor
        wrapMode: Text.NoWrap 
        font.family: textLayer.properties.fontFamily || "Arial"
        font.pixelSize: getScaledFontSize()
    }
}