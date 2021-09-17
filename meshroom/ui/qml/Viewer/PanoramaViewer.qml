import QtQuick 2.11
import Utils 1.0

import AliceVision 1.0 as AliceVision

/**
 * PanoramaViwer displays a list of Float Images
 * Requires QtAliceVision plugin.
 */

AliceVision.PanoramaViewer {
    id: root

    width: 3000
    height: 1500

    visible: (status === Image.Ready)

    // paintedWidth / paintedHeight / status for compatibility with standard Image
    property int paintedWidth: sourceSize.width
    property int paintedHeight: sourceSize.height
    property var status: {
        if (readyToLoad === Image.Ready) {
            return Image.Ready;
        }
        else {
            return Image.Null;
        }
    }

    property var readyToLoad: Image.Null

    property int subdivisionsPano: 12

    property bool isEditable: true

    property bool isHighlightable: true

    property bool displayGridPano: true

    property int mouseMultiplier: 1

    property bool cropFisheyePano: false

    property var idSelected : -1

    onIsHighlightableChanged:{
        for (var i = 0; i < repeater.model; ++i) {
            repeater.itemAt(i).item.onChangedHighlightState(isHighlightable);
        }
    }

    property alias containsMouse: mouseAreaPano.containsMouse

    property bool isRotating: false
    property var lastX : 0
    property var lastY: 0

    property var xStart : 0
    property var yStart : 0

    property double yaw: 0;
    property double pitch: 0;
    property double roll: 0;

    property var activeNode: _reconstruction.activeNodes.get('SfMTransform').node

    // Yaw and Pitch in Degrees from SfMTransform node sliders
    property int yawNode: activeNode.attribute("manualTransform.manualRotation.y").value;
    property int pitchNode: activeNode.attribute("manualTransform.manualRotation.x").value;
    property int rollNode: activeNode.attribute("manualTransform.manualRotation.z").value;

    //Convert angle functions
    function toDegrees(radians){
        return radians * (180/Math.PI)
    }

    function toRadians(degrees){
        return degrees * (Math.PI/180)
    }

    function fmod(a,b) { return Number((a - (Math.floor(a / b) * b)).toPrecision(8)); }

    // Limit angle between -180 and 180
    function limitAngle(angle){
        if (angle > 180) angle = -180.0 + (angle - 180.0);
        if (angle < -180) angle = 180.0 - (Math.abs(angle) - 180);
        return angle;
    }

    function limitPitch(angle)
    {
        return (angle > 180 || angle < -180) ? root.pitch : angle;
    }

    onYawNodeChanged: {
        root.yaw = yawNode;
    }
    onPitchNodeChanged: {
        root.pitch = pitchNode;
    }
    onRollNodeChanged: {
        root.roll = rollNode;
    }

    Item {
        id: containerPanorama
        z: 10
        Rectangle {
            width: 3000
            height: 1500
            color: "transparent"
            MouseArea {
                id: mouseAreaPano
                anchors.fill: parent
                hoverEnabled: true
                enabled: allImagesLoaded
                cursorShape: {
                    if (isEditable)
                        isRotating ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                }
                onPositionChanged: {
                    // Send Mouse Coordinates to Float Images Viewers
                    idSelected = -1;
                    for (var i = 0; i < repeater.model && isHighlightable; ++i) {
                        var highlight = repeater.itemAt(i).item.getMouseCoordinates(mouse.x, mouse.y);
                        repeater.itemAt(i).z = highlight ? 2 : 0
                        if(highlight){
                            idSelected = root.msfmData.viewsIds[i]
                        }
                    }

                    // Rotate Panorama
                    if (isRotating && isEditable) {
                        var xoffset = mouse.x - lastX;
                        var yoffset = mouse.y - lastY;
                        lastX = mouse.x;
                        lastY = mouse.y;

                        // Update Euler Angles
                        if (mouse.modifiers & Qt.AltModifier) {
                            root.roll = limitAngle(root.roll + toDegrees((xoffset / width) * mouseMultiplier))
                        }
                        else {
                            root.yaw = limitAngle(root.yaw + toDegrees((xoffset / width) * mouseMultiplier))
                            root.pitch = limitPitch(root.pitch + toDegrees(-(yoffset / height) * mouseMultiplier))
                        }

                        _reconstruction.setAttribute(activeNode.attribute("manualTransform.manualRotation.x"), Math.round(root.pitch));
                        _reconstruction.setAttribute(activeNode.attribute("manualTransform.manualRotation.y"), Math.round(root.yaw));
                        _reconstruction.setAttribute(activeNode.attribute("manualTransform.manualRotation.z"), Math.round(root.roll));
                    }
                }

                onPressed:{
                    _reconstruction.beginModification("Panorama Manual Rotation");
                    isRotating = true;
                    lastX = mouse.x;
                    lastY = mouse.y;

                    xStart = mouse.x;
                    yStart = mouse.y;
                }

                onReleased: {
                    _reconstruction.endModification();
                    isRotating = false;
                    lastX = 0
                    lastY = 0

                    //Select the image in the image gallery if clicked
                    if(xStart == mouse.x && yStart == mouse.y && idSelected != -1){
                        _reconstruction.selectedViewId = idSelected
                    }


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
                    for(var i=0; i < nrows+1; ++i){
                        ctx.moveTo(0, wgrid*i);
                        ctx.lineTo(width, wgrid*i);
                    }

                    var ncols = width/wgrid
                    for(var j=0; j < ncols+1; ++j){
                        ctx.moveTo(wgrid*j, 0);
                        ctx.lineTo(wgrid*j, height);
                    }

                    ctx.closePath()
                    ctx.stroke()
                }
            }
        }
    }

    property int imagesLoaded: 0
    property bool allImagesLoaded: false

    function loadRepeaterImages(index)
    {
        if (index < repeater.model)
            repeater.itemAt(index).loadItem();
        else
            allImagesLoaded = true;
    }


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
                property bool imageLoaded: false
                property bool loading: false

                onImageLoadedChanged: {
                    imagesLoaded++;
                    loadRepeaterImages(imagesLoaded);
                }

                function loadItem() {
                    if(!active)
                        return;

                    if (loading) {
                        loadRepeaterImages(index + 1)
                        return;
                    }

                    loading = true;

                    var idViewItem = msfmData.viewsIds[index]
                    var sourceItem = Filepath.stringToUrl(msfmData.getUrlFromViewId(idViewItem))

                    setSource("FloatImage.qml", {
                        'surface.viewerType': AliceVision.Surface.EViewerType.PANORAMA,
                        'viewerTypeString': 'panorama',
                        'surface.subdivisions': Qt.binding(function() { return subdivisionsPano; }),
                        'cropFisheye' : Qt.binding(function(){ return cropFisheyePano; }),
                        'surface.pitch': Qt.binding(function() { return root.pitch; }),
                        'surface.yaw': Qt.binding(function() { return root.yaw; }),
                        'surface.roll': Qt.binding(function() { return root.roll; }),
                        'index' : index,
                        'idView': Qt.binding(function() { return idViewItem; }),
                        'gamma': Qt.binding(function() { return hdrImageToolbar.gammaValue; }),
                        'gain': Qt.binding(function() { return hdrImageToolbar.gainValue; }),
                        'channelModeString': Qt.binding(function() { return hdrImageToolbar.channelModeValue; }),
                        'downscaleLevel' : Qt.binding(function() { return downscale; }),
                        'source':  Qt.binding(function() { return sourceItem; }),
                        'surface.msfmData': Qt.binding(function() { return root.msfmData }),
                        'canBeHovered': true
                    })
                    imageLoaded = Qt.binding(function() { return repeater.itemAt(index).item.status === Image.Ready ? true : false; })
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
            onDownscaleReady: {
                root.imagesLoaded = 0;

                // Retrieve downscale value from C++
                panoramaViewerToolbar.updateDownscaleValue(root.downscale)

                //Changing the repeater model (number of elements)
                panoImages.updateRepeater()

                root.readyToLoad = Image.Ready;

                // Load images two by two
                loadRepeaterImages(0);
                loadRepeaterImages(1);
            }
        }

        function updateRepeater() {
            if(repeater.model !== root.msfmData.viewsIds.length){
                repeater.model = 0;
            }
            repeater.model = root.msfmData.viewsIds.length;
        }
    }



}
