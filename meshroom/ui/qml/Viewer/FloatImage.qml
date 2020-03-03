import QtQuick 2.11
import Utils 1.0

import AliceVision 1.0 as AliceVision

/**
 * FloatImage displays an Image with gamma / offset / channel controls
 * Requires QtAliceVision plugin.
 */

AliceVision.FloatImageViewer {
    id: root

    width: textureSize.width
    height: textureSize.height
    visible: (status === Image.Ready)

    // paintedWidth / paintedHeight / status for compatibility with standard Image
    property int paintedWidth: textureSize.width
    property int paintedHeight: textureSize.height
    property var status: {
        if(root.loading)
            return Image.Loading;
        else if((root.source === "") ||
                (root.sourceSize.height <= 0) ||
                (root.sourceSize.height <= 0))
            return Image.Null;
        return Image.Ready;
    }

    property string channelModeString : "rgba"

    channelMode: {
        switch(channelModeString)
        {
            case "rgb": return AliceVision.FloatImageViewer.EChannelMode.RGB
            case "r": return AliceVision.FloatImageViewer.EChannelMode.R
            case "g": return AliceVision.FloatImageViewer.EChannelMode.G
            case "b": return AliceVision.FloatImageViewer.EChannelMode.B
            case "a": return AliceVision.FloatImageViewer.EChannelMode.A
            default: return AliceVision.FloatImageViewer.EChannelMode.RGBA
        }
    }
    clearBeforeLoad: true

    property alias containsMouse: mouseArea.containsMouse
    property alias mouseX: mouseArea.mouseX
    property alias mouseY: mouseArea.mouseY
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
    }
}
