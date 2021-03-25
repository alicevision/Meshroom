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
    height: 1500
    visible: (status === Image.Ready)

    // paintedWidth / paintedHeight / status for compatibility with standard Image
    property int paintedWidth: textureSize.width
    property int paintedHeight: textureSize.height
    property var status: {
        if (readyToLoad === Image.Ready && root.imagesLoaded === root.pathList.length) {
            for (var i = 0; i < repeater.model; i++) {
                if (repeater.itemAt(i).item.status !== Image.Ready) return Image.Loading;
            }
            return Image.Ready;
        }
        else if (readyToLoad === Image.Ready) {
            return Image.Loading;
        }
        else {
            return Image.Null;
        }
    }
    property var readyToLoad: Image.Null

    // Value from ui button
    property int downscaleValueQML: 0

    // Value from cpp at initialisation
    property int downscaleValueCpp: 0

    property int subdivisionsPano: 12

    property bool isEditable: true
    property bool isHighlightable: true

    property bool displayGridPano: true

    property int mouseMultiplier: 1

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

    onDownscaleValueQMLChanged: {
        for (var i = 0; i < repeater.model; i++) {
           repeater.itemAt(i).item.downscaleLevel = downscaleValueQML;
        }
    }

    clearBeforeLoad: true

    property alias containsMouse: mouseAreaPano.containsMouse

    property bool isRotating: false
    property var lastX : 0
    property var lastY: 0

    property int yaw: 0;
    property int pitch: 0;

    // Yaw and Pitch in Degrees from SfMTransform sliders
    property int yawNode: _reconstruction.activeNodes.get('SfMTransform').node.attribute("manualTransform.manualRotation.y").value;
    property int pitchNode: _reconstruction.activeNodes.get('SfMTransform').node.attribute("manualTransform.manualRotation.x").value;


    onYawNodeChanged: {
        if (!isRotating) {
            for (var i = 0; i < repeater.model; i++) {
               repeater.itemAt(i).item.rotatePanoramaDegrees(yawNode, pitchNode);
            }
        }
    }

    onPitchNodeChanged: {
       if (!isRotating) {
           for (var i = 0; i < repeater.model; i++) {
              repeater.itemAt(i).item.rotatePanoDegrees(yawNode, pitchNode);
           }
       }
    }


    Item {
        id: containerPanorama
        z: 10
        Rectangle {
            width: 3000
            height: 1500
            //color: mouseAreaPano.containsMouse? "red" : "green"
            color: "transparent"
            MouseArea {
                id: mouseAreaPano
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: {
                    if (isEditable)
                        isRotating ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                }
                onPositionChanged: {
                    // Send Mouse Coordinates to Float Images Viewers
                    for (var i = 0; i < repeater.model && isHighlightable; i++) {
                        var highlight = repeater.itemAt(i).item.getMouseCoordinates(mouse.x, mouse.y);
                        repeater.itemAt(i).z = highlight ? 2 : 0
                        if (highlight)
                        {
                            // Disable Highlight for all images next to the highlight one
                            for (let j = i + 1; j < repeater.model; j++)
                            {
                                repeater.itemAt(j).item.mouseOver(false);
                                repeater.itemAt(i).z = 0;
                            }
                            break;
                        }
                    }

                    // Rotate Panorama
                    if (isRotating && isEditable) {
                        var xoffset = mouse.x - lastX;
                        var yoffset = mouse.y - lastY;
                        lastX = mouse.x;
                        lastY = mouse.y;
                        for (var i = 0; i < repeater.model; i++) {
                           repeater.itemAt(i).item.rotatePanoRadians((xoffset / width) * mouseMultiplier, -(yoffset / height) * mouseMultiplier);
                        }
                    }
                }

                onPressed:{
                    isRotating = true;
                    lastX = mouse.x;
                    lastY = mouse.y;
                }

                onReleased: {
                    if (isRotating)
                    {
                        // Update Euler angles
                        var activeNode = _reconstruction.activeNodes.get('SfMTransform').node;

                        root.yaw = repeater.itemAt(0).item.getYaw();
                        root.pitch = repeater.itemAt(0).item.getPitch();

                        activeNode.attribute("manualTransform.manualRotation.y").value = root.yaw;
                        activeNode.attribute("manualTransform.manualRotation.x").value = root.pitch;
                    }

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
        var activeNode = _reconstruction.activeNodes.get('SfMTransform').node;

        if(!activeNode)
        {
            root.sfmPath = "";
        }
        else
        {
            root.sfmPath = activeNode.attribute("input").value;
        }
        root.setSfmPath(sfmPath);
    }

    property var pathList : []
    property var idList : []
    property int imagesLoaded: 0

    Item {
        id: panoImages
        width: root.width
        height: root.height

        Component {
            id: imgPano
            Loader {
                id: floatOneLoader
                active: root.readyToLoad
                visible: (floatOneLoader.status === Loader.Ready)
                z:0
                //anchors.centerIn: parent
                property string cSource: Filepath.stringToUrl(root.pathList[index].toString())
                property int cId: root.idList[index]
                onActiveChanged: {
                    if(active) {
                        setSource("FloatImage.qml", {
                            'isPanoViewer' : true,
                            'downscaleLevel' : root.downscaleValueCpp,
                            'source':  Qt.binding(function() { return cSource; }),
                            'index' : index,
                            'idView': Qt.binding(function() { return cId; }),
                        })

                    } else {
                        // Force the unload (instead of using Component.onCompleted to load it once and for all) is necessary since Qt 5.14
                        setSource("", {})
                    }
                }
                onLoaded: {
                    imagesLoaded++;
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
                root.imagesLoaded = 0;
                //We receive the map<ImgPath, idView> from C++
                //Resetting arrays to avoid problem with push

                //Iterating through the map
                for (var path in imagesData) {
                    if (path === "lvl") {
                        root.downscaleValueCpp = imagesData[path];
                        panoramaViewerToolbar.updateDownscaleValue(root.downscaleValueCpp)
                        continue;
                    }

                    root.pathList.push(path)
                    root.idList.push(imagesData[path])
                }

                //Changing the repeater model (number of elements)
                panoImages.updateRepeater()

                root.readyToLoad = Image.Ready;
            }
        }

        function updateRepeater() {
            if(repeater.model !== root.pathList.length){
                repeater.model = 0;
            }
            repeater.model = root.pathList.length;
        }
    }



}
