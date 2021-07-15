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

    property var sfmData

    onSfmDataChanged: {
        console.warn("FLOAT IMG " + sfmData)
        root.surface.msfmData = sfmData;
    }


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
        if (viewerTypeString === "panorama") {
            surface.rotateSurfaceDegrees(
                _reconstruction.activeNodes.get('SfMTransform').node.attribute("manualTransform.manualRotation.y").value,
                _reconstruction.activeNodes.get('SfMTransform').node.attribute("manualTransform.manualRotation.x").value)
        }
        root.surface.setIdView(idView);
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

    property string viewerTypeString : "hdr"
    surface.viewerType: {
        switch(viewerTypeString)
        {
            case "hdr": return AliceVision.Surface.EViewerType.HDR;
            case "distortion": return AliceVision.Surface.EViewerType.DISTORTION;
            case "panorama": return AliceVision.Surface.EViewerType.PANORAMA;
            default: return AliceVision.Surface.EViewerType.HDR;
        }
    }

    property bool isPrincipalPointsDisplayed : false;
    property int pointsNumber: (surface.subdivisions + 1) * (surface.subdivisions + 1);

    property int index: 0;
    property var idView: 0;

    function updatePrincipalPoint() {
        var pp = root.surface.getPrincipalPoint();
        ppRect.x = pp.x;
        ppRect.y = pp.y;
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
            visible: viewerTypeString === "distortion" && isPrincipalPointsDisplayed
        }

        Connections {
            target: root
            onSfmChanged: {
                if (viewerTypeString === "distortion")
                    updatePrincipalPoint();
            }
        }
    }
}
