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

    property var paths: ["L:/IMAC/IMAC2/PTUT/22_190902_GDGM_F1_sph150/HDM_1306.JPG", "L:/IMAC/IMAC2/PTUT/22_190902_GDGM_F1_sph150/HDM_1313.JPG"]



    Item {
        id: panoImages
        width: root.width
        height: root.height

        function setSource() {
            if (repeater.model === 0)
                return

//            var width = repeater.itemAt(0).width;
//            var height = repeater.itemAt(0).height;

            for (let i = 0; i < repeater.model; i++) {
                console.warn(repeater.itemAt(i))
//                repeater.itemAt(i).x = root.getVertex(i).x - (width / 2);
//                repeater.itemAt(i).y = root.getVertex(i).y - (height / 2);
            }
        }

        Component {
            id: imgPano
            Loader {
                id: floatOneLoader
                active: root.status
                visible: (floatOneLoader.status === Loader.Ready)
                //anchors.centerIn: parent
                property string cSource: Filepath.stringToUrl(root.paths[index].toString())
                onActiveChanged: {
                    if(active) {
                        setSource("FloatImage.qml", {
                            'source':  Qt.binding(function() { return cSource; }),
                            'index' : index
                        })
                        console.warn(cSource)
                        console.warn(root.source)
                    } else {
                        // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                        setSource("", {})
                    }
                }
                onLoaded: {
                    //console.warn(repeater.itemAt(index))
                    repeater.itemAt(index).x = repeater.itemAt(0).width + 50* index
                }
            }
        }
        Repeater {
            id: repeater
            model: 2
            delegate: imgPano

        }
    }



}
