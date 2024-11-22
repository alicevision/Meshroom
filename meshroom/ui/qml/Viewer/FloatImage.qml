import QtQuick

import AliceVision 1.0 as AliceVision
import Utils 1.0

/**
 * FloatImage displays an Image with gamma / offset / channel controls
 * Requires QtAliceVision plugin.
 */

AliceVision.FloatImageViewer {
    id: root

    width: sourceSize.width
    height: sourceSize.height
    visible: true

    // paintedWidth / paintedHeight / imageStatus for compatibility with standard Image
    property int paintedWidth: sourceSize.width
    property int paintedHeight: sourceSize.height
    property var imageStatus: {
        if (root.status === AliceVision.FloatImageViewer.EStatus.LOADING) {
            return Image.Loading
        } else if (root.status === AliceVision.FloatImageViewer.EStatus.LOADING_ERROR ||
                   root.status === AliceVision.FloatImageViewer.EStatus.MISSING_FILE ||
                   root.status === AliceVision.FloatImageViewer.EStatus.OUTDATED_LOADING) {
            return Image.Error
        } else if ((root.source === "") || (root.sourceSize.height <= 0) || (root.sourceSize.width <= 0)) {
            return Image.Null
        }

        return Image.Ready
    }

    onStatusChanged: {
        if (viewerTypeString === "panorama") {
            var activeNode = _reconstruction.activeNodes.get('SfMTransform').node
        }
        root.surface.setIdView(idView);
    }

    property string channelModeString : "rgba"
    channelMode: {
        switch (channelModeString) {
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
        switch (viewerTypeString) {
            case "hdr": return AliceVision.Surface.EViewerType.HDR;
            case "distortion": return AliceVision.Surface.EViewerType.DISTORTION;
            case "panorama": return AliceVision.Surface.EViewerType.PANORAMA;
            default: return AliceVision.Surface.EViewerType.HDR;
        }
    }

    property int pointsNumber: (surface.subdivisions + 1) * (surface.subdivisions + 1)

    property int idView: 0;

    clearBeforeLoad: false

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
        return root.surface.isMouseInside(mx, my)
    }

    function getMouseCoordinates(mx, my) {
        if (isMouseOver(mx, my)) {
            root.surface.mouseOver = true
            return true
        } else {
            root.surface.mouseOver = false
            return false
        }
    }

    function onChangedHighlightState(isHighlightable) {
        if (!isHighlightable) root.surface.mouseOver = false
    }

    /*
    * Principal Point
    */

    function updatePrincipalPoint() {
        var pp = root.surface.getPrincipalPoint()
        ppRect.x = pp.x
        ppRect.y = pp.y
    }

    property bool isPrincipalPointsDisplayed : false

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
            onVisibleChanged: {
                updatePrincipalPoint()
            }
        }
    }
}
