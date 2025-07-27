import QtQuick
import QtQuick.Shapes

/**
* TextShape
*
* @biref Display a text with the given properties.
* @param properties - the given shape style properties
* @param observation - the given shape information for the current view id
*/
BaseShape {
    id: textRoot

    x: textRoot.observation.centerX - (textArea.implicitWidth * 0.5)   // center text horizontally
    y: textRoot.observation.centerY - (textArea.implicitHeight * 0.5)  // center text vertically

    Text {
        id: textArea
        text: textRoot.observation.content || "Undefined"
        color: textRoot.properties.color || textRoot.defaultStrokeColor
        wrapMode: Text.NoWrap 
        font.family: textRoot.properties.fontFamily || "Arial"
        font.pixelSize: (textRoot.properties.fontSize || 10) * textRoot.parent.scaleRatio
    }
}