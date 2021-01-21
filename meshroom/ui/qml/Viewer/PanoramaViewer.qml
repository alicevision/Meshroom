import QtQuick 2.11
import Utils 1.0

import AliceVision 1.0 as AliceVision

/**
 * FloatImage displays an Image with gamma / offset / channel controls
 * Requires QtAliceVision plugin.
 */

AliceVision.PanoramaViewer {
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
                (root.sourceSize.width <= 0))
            return Image.Null;
        root.defaultControlPoints();
        return Image.Ready;
    }

    clearBeforeLoad: true

    channelMode : AliceVision.PanoramaViewer.EChannelMode.RGBA

    property alias containsMouse: mouseArea.containsMouse
    property alias mouseX: mouseArea.mouseX
    property alias mouseY: mouseArea.mouseY
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        // Do not intercept mouse events, only get the mouse over information
        acceptedButtons: Qt.NoButton
    }

    property string sfmPath: ""

    function updateSfmPath() {
        var activeNode = _reconstruction.activeNodes.get('sfm').node;

        if(!activeNode)
        {
            root.sfmPath = "";
        }
        else
        {
            root.sfmPath = activeNode.attribute("outputViewsAndPoses").value;
        }
        root.setSfmPath(sfmPath);
    }

    Component {
        id: imgPano
        Loader {
            id: floatOneLoader
            active: root.status
            visible: (floatOneLoader.status === Loader.Ready)
            anchors.centerIn: parent
            property string cSource: root.getImgSource()
            onActiveChanged: {
                if(active) {
                    setSource("FloatImage.qml", {
                        'source':  Qt.binding(function() { return cSource; }),
                    })
                } else {
                    // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                    setSource("", {})
                }
            }
        }
    }

    Repeater {
        id: repeater
        model: 1
        delegate: imgPano
    }


}
