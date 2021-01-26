import QtQuick 2.11
import Utils 1.0

import AliceVision 1.0 as AliceVision

/**
 * FloatImage displays an Image with gamma / offset / channel controls
 * Requires QtAliceVision plugin.
 */

AliceVision.PanoramaViewer {
    id: root

    width: 3000
    height: 1000
    visible: (status === Image.Ready)

    // paintedWidth / paintedHeight / status for compatibility with standard Image
    property int paintedWidth: textureSize.width
    property int paintedHeight: textureSize.height
    property var status: Image.Null

    property int downscaleValue: 2

    property int subdivisionsPano: 12

    property bool isEditable: true
    property bool isHighlightable: true

    property bool displayGridPano: true

    onIsHighlightableChanged:{
        for (var i = 0; i < repeater.model; i++) {
            repeater.itemAt(i).item.onChangedHighlightState(isHighlightable);
        }
    }

    onSubdivisionsPanoChanged:{
        for (var i = 0; i < repeater.model; i++) {
           repeater.itemAt(i).item.updateSubdivisions(subdivisionsPano);
        }
    }

    onDownscaleValueChanged: {
        for (var i = 0; i < repeater.model; i++) {
           repeater.itemAt(i).item.setDownscale(downscaleValue);
        }
    }

    clearBeforeLoad: true

    property alias containsMouse: mouseAreaPano.containsMouse

    property bool isRotating: false
    property var lastX : 0
    property var lastY: 0

    Item {
        id: containerPanorama
        z: 10
        Rectangle {
            width: 3000
            height: 1000
            //color: mouseAreaPano.containsMouse? "red" : "green"
            color: "transparent"
            MouseArea {
                id: mouseAreaPano
                anchors.fill: parent
                hoverEnabled: true

                onPositionChanged: {
                    // Send Mouse Coordinates to Float Images Viewers
                    for (var i = 0; i < repeater.model && isHighlightable; i++) {
                        var highlight = repeater.itemAt(i).item.getMouseCoordinates(mouse.x, mouse.y);
                        repeater.itemAt(i).z = highlight ? 2 : 0
                    }

                    // Rotate Panorama
                    if (isRotating && isEditable) {
                        var xoffset = mouse.x - lastX;
                        var yoffset = mouse.y - lastY;
                        lastX = mouse.x;
                        lastY = mouse.y;
                        for (var i = 0; i < repeater.model; i++) {
                            repeater.itemAt(i).item.rotatePanorama(xoffset * 0.001, yoffset*0.001)
                        }
                    }
                }

                onPressed:{
                    isRotating = true;
                    lastX = mouse.x;
                    lastY = mouse.y;
                }

                onReleased: {
                    isRotating = false;
                    lastX = 0
                    lastY = 0
                }
            }

            // Grid Panorama Viewer
            Canvas {
                id: gridPano
                visible: displayGridPano
                anchors.fill : parent
                property int wgrid: 40
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.lineWidth = 1.0
                    ctx.shadowBlur = 0
                    ctx.strokeStyle = "grey"
                    var nrows = height/wgrid;
                    for(var i=0; i < nrows+1; i++){
                        ctx.moveTo(0, wgrid*i);
                        ctx.lineTo(width, wgrid*i);
                    }

                    var ncols = width/wgrid
                    for(var j=0; j < ncols+1; j++){
                        ctx.moveTo(wgrid*j, 0);
                        ctx.lineTo(wgrid*j, height);
                    }

                    ctx.closePath()
                    ctx.stroke()
                }
            }
        }
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

    property var pathList : []
    property var idList : []

    Item {
        id: panoImages
        width: root.width
        height: root.height

        Component {
            id: imgPano
            Loader {
                id: floatOneLoader
                active: root.status
                visible: (floatOneLoader.status === Loader.Ready)
                z:0
                //anchors.centerIn: parent
                property string cSource: Filepath.stringToUrl(root.pathList[index].toString())
                property int cId: root.idList[index]
                onActiveChanged: {
                    if(active) {
                        setSource("FloatImage.qml", {
                            'isPanoViewer' : true,
                            'source':  Qt.binding(function() { return cSource; }),
                            'index' : index,
                            'idView': Qt.binding(function() { return cId; }),
                        })
                        console.warn(cSource)
                    } else {
                        // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                        setSource("", {})
                    }
                }
            }
        }
        Repeater {
            id: repeater
            model: 0
            delegate: imgPano

        }
        Connections {
            target: root
            onImagesDataChanged: {
                //We receive the map<ImgPath, idView> from C++
                console.warn("IMAGES DATA CHANGED ! " + imagesData)

                //Resetting arrays to avoid problem with push
                pathList = []
                idList = []

                //Iterating through the map
                for (var path in imagesData) {
                    console.warn("Object item:", path, "=", imagesData[path])
                    root.pathList.push(path)
                    root.idList.push(imagesData[path])
                }
                console.warn(root.pathList.length)

                //Changing the repeater model (number of elements)
                panoImages.updateRepeater()

                root.status = Image.Ready;
            }
        }
        function updateRepeater() {
            if(repeater.model !== root.pathList.length){
                repeater.model = 0;
            }
            //console.warn(imagesData.length)
            repeater.model = root.pathList.length;
        }
    }



}
