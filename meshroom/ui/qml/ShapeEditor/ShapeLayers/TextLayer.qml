import QtQuick

/**
* TextLayer
*
* @biref Allows to display a text.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param selected - the shape is selected
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @see BaseShapeLayer.qml
*/
BaseShapeLayer {
    id: root

    Text {
        x: root.observation.centerX - implicitWidth * 0.5   // center text horizontally
        y: root.observation.centerY - implicitHeight * 0.5  // center text vertically
        text: root.observation.content || "Undefined"
        color: root.properties.color || root.defaultColor
        wrapMode: Text.NoWrap 
        font.family: root.properties.fontFamily || "Arial"
        font.pixelSize: getScaledFontSize()
    }
}