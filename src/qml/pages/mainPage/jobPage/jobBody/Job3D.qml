import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.GL 0.1

Item {
    Menu {
        id: menu

        ExclusiveGroup { id: selectionModeGroup }

        MenuItem {
            text: "Select plane"
            exclusiveGroup: selectionModeGroup
            checkable: true
            checked: true
            onCheckedChanged: if (checked) glview.selectionMode = GLView.RECTANGLE
        }

        MenuItem {
            text: "Select line"
            exclusiveGroup: selectionModeGroup
            checkable: true
            onCheckedChanged: if (checked) glview.selectionMode = GLView.LINE
        }

        MenuSeparator {}

        MenuItem {
            text: "Define ground plane"
            onTriggered: glview.definePlane()
        }
        MenuItem {
            text: "Flip plane normal"
            onTriggered: glview.flipPlaneNormal()
        }
        MenuItem {
            text: "Define ground orientation"
            onTriggered: orientationDialog.open()
        }

        MenuItem {
            text: "Clear plane"
            onTriggered: glview.clearPlane()
        }

        MenuSeparator {}


        MenuItem {
            text: "Define scale"
            onTriggered: distanceDialog.open()
        }
        MenuItem {
            text: "Reset scale"
            onTriggered: glview.resetScale()
        }

        MenuSeparator {}

        MenuItem {
            text: "Get parameters"
            onTriggered: cmdlineDialog.open()
        }
    }

    Dialog {
        id: distanceDialog
        Row {
            anchors.fill: parent
            spacing: 2
            Label { text: "Distance " }
            TextInput {
                id: scaleFactor
                text: "1.0"
            }
        }
        onVisibleChanged: if (visible) scaleFactor.text = glview.scale
        onAccepted: {
            var scale = parseFloat(scaleFactor.text);
            if (!isNaN(scale)) glview.defineScale(scale);
            else console.log("Scale must be a number");
        }
    }

    Dialog {
        id: orientationDialog
        Row {
            anchors.fill: parent
            spacing: 2
            Label { text: "Rotation (deg)" }
            TextInput {
                id: yrot
                text: "0.0"
            }
        }
        onVisibleChanged: if (visible) yrot.text = glview.yrot
        onAccepted: {
            var deg = parseFloat(yrot.text);
            if (!isNaN(deg)) glview.yrot = deg;
            else console.log("Rotation must be a number");
        }
    }

    Dialog {
        id: cmdlineDialog
        TextInput {
            id: cmdparams
        }
        onVisibleChanged: {
            var n = glview.planeNormal;
            cmdparams.text = '\'%1,%2,%3;%4;%5\''.arg(n.x).arg(n.y).arg(n.z).arg(glview.yrot).arg(glview.scale);
        }
    }

    DropArea {
        anchors.fill: parent
        hideBackground: true
        onDropped: glview.loadAlembicScene(drop.urls[0])
        GLView {
            id: glview
            anchors.fill: parent
            color: "#333"
            property variant job: currentJob
            onJobChanged: glview.loadAlembicScene(Qt.resolvedUrl(currentJob.url+"/"+currentJob.name+".abc"))
            onOpenPopup: menu.popup()
        }
    }
    Connections {
        target: _applicationWindow
        onShowCameras: {
            glview.showCameras = checked
        }
        onShowGrid: {
            glview.showGrid = checked
        }
    }
}
