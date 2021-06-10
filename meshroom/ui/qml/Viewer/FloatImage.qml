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

    onStatusChanged: {
        if(isPanoViewer) { // Pano Viewer
            root.updateSubdivisions(12)
        }
        else if (!isDistoViewer){ // HDR Viewer
            root.updateSubdivisions(1);
        }

        root.surface.setIdView(idView);
        updateSfmPath();
    }

    property string channelModeString : "rgba"

    property string viewerTypeString : "default"

    property bool isDistoViewer: false;
    property bool isPanoViewer: false;

    property int gridOpacity : 100;

    property bool isPrincipalPointsDisplayed : false;
    property int subdivisions: 4;
    property int pointsNumber: (subdivisions + 1) * (subdivisions + 1);

    property int index: 0;
    property var idView: 0;

    function updateSfmPath() {
        var activeNode = _reconstruction.activeNodes.get('SfMTransform').node;
        root.surface.sfmPath = activeNode ? activeNode.attribute("input").value : "";
    }

    function updatePrincipalPoint() {
        var pp = root.surface.getPrincipalPoint();
        ppRect.x = pp.x;
        ppRect.y = pp.y;
    }

    onIsDistoViewerChanged: {

        //root.hasDistortion(isDistoViewer);
        surface.viewerType = AliceVision.Surface.EViewerType.DISTORTION;

        //Putting states back where they were
        if(isDistoViewer){
            root.updateSubdivisions(subdivisions)
        }
        //Forcing disabling of parameters
        else{

            root.updateSubdivisions(1)
        }
    }

    onIsPanoViewerChanged: {
        surface.viewerType = AliceVision.Surface.EViewerType.PANORAMA;
    }

    onSubdivisionsChanged: {
        pointsNumber = (subdivisions + 1) * (subdivisions + 1);
        root.updateSubdivisions(subdivisions)
    }

    onGridOpacityChanged: {
        root.surface.gridColor = Qt.rgba(root.surface.gridColor.r, root.surface.gridColor.g, root.surface.gridColor.b, gridOpacity/100);
    }

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
        // Do not intercept mouse events, only get the mouse over information
        acceptedButtons: Qt.NoButton
    }

    function isMouseOver(mx, my) {
        return root.surface.isMouseInside(mx, my);
    }

    function getMouseCoordinates(mx, my) {
        if (isMouseOver(mx, my)) {
            root.surface.mouseOver = true
            return true;
        } else {
            root.surface.mouseOver = false
            return false;
        }
    }

    function onChangedHighlightState(isHighlightable){
        if (!isHighlightable) root.surface.mouseOver = false
    }


    /*
    * Principal Point
    */
    Item {
        id: principalPoint
        Rectangle {
            id: ppRect
            width: root.sourceSize.width/150; height: width
            radius : width/2
            x: 0
            y: 0
            color: "red"
            visible: isDistoViewer && isPrincipalPointsDisplayed
        }

        Connections {
            target: root
            onSfmChanged: {
                if (isDistoViewer)
                    updatePrincipalPoint();
            }
        }
    }
}
