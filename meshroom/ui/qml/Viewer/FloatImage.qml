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

        if(!isDistoViewer){
            if(isPanoViewer){
                root.updateSubdivisions(12)
            }
            else{
                root.updateSubdivisions(1);
                root.downscaleLevel = -1;
            }
        }

        root.defaultControlPoints();
        root.setIdView(idView);
        updateSfmPath();
        updateMouseAreaPano();

        return Image.Ready;
    }

    property string channelModeString : "rgba"

    property bool isDistoViewer: false;
    property bool isPanoViewer: false;

    property bool isGridDisplayed : false;
    property int gridOpacity : 100;
    property color gridColor : "#FF0000";

    property bool isCtrlPointsDisplayed : true;
    property int subdivisions: 4;
    property int pointsNumber: (subdivisions + 1) * (subdivisions + 1);

    property int index: 0;
    property var idView: 0;

    property string sfmPath: ""

    property int downscaleLevel: 0

    onDownscaleLevelChanged: {
        root.setDownscale(downscaleLevel)
        console.warn("VALUE CHANGGGEEEEEEEEEEEEED " + downscaleLevel)
    }

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

    function updatePrincipalPoint() {
        var pp = root.getPrincipalPoint();
        ppRect.x = pp.x;
        ppRect.y = pp.y;
    }

    function rotatePanoDegrees(yaw, pitch) {
        root.rotatePanoramaDegrees(yaw, pitch);
    }

    function rotatePanoRadians(yaw, pitch) {
        root.rotatePanoramaRadians(yaw, pitch);
    }

    function updateMouseAreaPano() {
        var coords = root.getMouseAreaPanoCoords()

        rectPano.x = coords[0] + 25
        rectPano.y = coords[1] + 25
        rectPano.width = coords[2] - 25
        rectPano.height = coords[3] - 25
    }

    onIsDistoViewerChanged: {
        root.hasDistortion(isDistoViewer);
        //Putting states back where they were
        if(isDistoViewer){
            root.displayGrid(isGridDisplayed);
            repeater.displayControlPoints(isCtrlPointsDisplayed)
            root.updateSubdivisions(subdivisions)
        }
        //Forcing disabling of parameters
        else{
            root.displayGrid(isDistoViewer)
            repeater.displayControlPoints(isDistoViewer)
            root.updateSubdivisions(1)
        }
    }

    onIsPanoViewerChanged: {
        root.setPanoViewerEnabled(isPanoViewer)
    }

    onIsGridDisplayedChanged: {
        root.displayGrid(isGridDisplayed);
    }

    onSubdivisionsChanged: {
        pointsNumber = (subdivisions + 1) * (subdivisions + 1);
        root.updateSubdivisions(subdivisions)
    }

    onIsCtrlPointsDisplayedChanged: {
         repeater.displayControlPoints(isCtrlPointsDisplayed)
    }

    onGridOpacityChanged: {
        root.setGridColorQML(Qt.rgba(gridColor.r, gridColor.g, gridColor.b, gridOpacity/100));
    }

    onGridColorChanged: {
        root.setGridColorQML(Qt.rgba(gridColor.r, gridColor.g, gridColor.b, gridOpacity/100));
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

//    property alias containsMouse: mouseArea.containsMouse
//    property alias mouseX: mouseArea.mouseX
//    property alias mouseY: mouseArea.mouseY
//    MouseArea {
//        id: mouseArea
//        anchors.fill: parent
//        hoverEnabled: true
//        // Do not intercept mouse events, only get the mouse over information
//        acceptedButtons: Qt.NoButton
//    }

    function isMouseOver(mx, my) {
        return (mx > rectPano.x && mx < rectPano.x + rectPano.width
                && my > rectPano.y && my < rectPano.y + rectPano.height)
    }

    function getMouseCoordinates(mx, my) {
        if (isMouseOver(mx, my)) {
            root.mouseOver(true)
            return true;
        } else {
            root.mouseOver(false)
            return false;
        }
    }

    function onChangedHighlightState(isHighlightable){
        if(isHighlightable) root.mouseOver(false)
        else root.mouseOver(true)
    }

    /*
    * Target Rectangle For Mouse Area Highlight
    */
    Item {
        id: containerMouseAreaPano
        Rectangle {
            id: rectPano
            x: 0
            y: 0
            width: 0
            height: 0
            visible: false;
        }
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
            visible: isDistoViewer && isCtrlPointsDisplayed
        }

        Connections {
            target: root
            onSfmChanged: {
                if (isDistoViewer)
                    updatePrincipalPoint();
            }
        }
    }

    /*
    * Controls Points
    */
    Item {
        id: points
        width: root.width
        height: root.height

        Connections {
            target: root
            onVerticesChanged : {
                if (reinit){
                   points.recalculateCP();
                   points.generateControlPoints();
                   root.updateMouseAreaPano()
                }
            }
        }

        function generateControlPoints() {
            if(repeater.model === pointsNumber){
                repeater.model = 0;
            }
            repeater.model = pointsNumber;
        }

        function recalculateCP() {
            if (repeater.model === 0)
                return

            var width = repeater.itemAt(0).width;
            var height = repeater.itemAt(0).height;

            for (let i = 0; i < repeater.model; i++) {
                repeater.itemAt(i).x = root.getVertex(i).x - (width / 2);
                repeater.itemAt(i).y = root.getVertex(i).y - (height / 2);
            }
        }

        Component {
            id: point
            Rectangle {
                id: rect
                width: root.sourceSize.width/100; height: width
                radius: width/2
                x: root.getVertex(model.index).x - (width / 2)
                y: root.getVertex(model.index).y - (height / 2)
                color: Colors.yellow
                visible: isDistoViewer && isCtrlPointsDisplayed
                MouseArea {
                    id: mouseAreaCP
                    anchors.fill : parent;
                    acceptedButtons: Qt.LeftButton

                    drag.target: rect
                    drag.smoothed: false
                    drag.axis: Drag.XAndYAxis
                    onReleased: {
                        root.setVertex(index, rect.x + (width / 2), rect.y + (height / 2))
                    }
                }
            }
        }

        Repeater {
            id: repeater
            model: pointsNumber
            delegate: point
            function displayControlPoints(state) {
                for (let i = 0; i < model; i++) {
                    if (repeater.itemAt(i) !== null)
                        repeater.itemAt(i).visible = state;
                }
            }
        }
    }
}
