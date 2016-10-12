import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Rectangle {

    id: root
    color: Qt.rgba(0, 0, 0, 0.2)
    clip: true

    function fit() {
        if(image.status != Image.Ready)
            return;
        image.scale = Math.min(root.width/image.width, root.height/image.height)
        image.x = Math.max((root.width-image.width*image.scale)*0.5, 0)
        image.y = Math.max((root.height-image.height*image.scale)*0.5, 0)
    }

    property Component contextMenu: Menu {
        MenuItem {
            text: "Fit"
            onTriggered: fit()
        }
        MenuItem {
            text: "Zoom 100%"
            onTriggered: image.scale = 1
        }
    }

    Rectangle { // placeholder
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height*1.5) * 0.95 // 5% margin
        height: Math.min(parent.height, parent.width*1.5) * 0.95 // 5% margin
        color: "transparent"
        border.color: "#333"
        visible: image.status != Image.Ready
    }

    Image {
        id: image
        transformOrigin: Item.TopLeft
        asynchronous: true
        smooth: false
        fillMode: Image.PreserveAspectFit
        onWidthChanged: if(status==Image.Ready) fit()
    }

    Label {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 2
        text: image.scale.toFixed(1) + "x"
        state: "xsmall"
    }

    MouseArea {
        anchors.fill: parent
        drag.target: image
        property double factor: 1.5
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if(mouse.button & Qt.RightButton) {
                var menu = contextMenu.createObject(root);
                menu.x = mouse.x;
                menu.y = mouse.y;
                menu.open()
            }
        }
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            if(Math.min(image.width*image.scale*zoomFactor, image.height*image.scale*zoomFactor) < 10)
                return
            var point = mapToItem(image, wheel.x, wheel.y)
            image.x += (1-zoomFactor) * point.x * image.scale
            image.y += (1-zoomFactor) * point.y * image.scale
            image.scale *= zoomFactor
        }
    }

    BusyIndicator {
        anchors.centerIn: parent
        running: image.status === Image.Loading
    }
}
