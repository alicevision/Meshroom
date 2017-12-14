import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

FocusScope {
    id: root

    clip: true
    property alias source: image.source

    // slots
    Keys.onPressed: {
        if(event.key == Qt.Key_F) {
            root.fit();
            event.accepted = true;
        }
    }

    // functions
    function fit() {
        if(image.status != Image.Ready)
            return;
        image.scale = Math.min(root.width/image.width, root.height/image.height)
        image.x = Math.max((root.width-image.width*image.scale)*0.5, 0)
        image.y = Math.max((root.height-image.height*image.scale)*0.5, 0)
    }

    // context menu
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

    // Main Image
    Image {
        id: image
        transformOrigin: Item.TopLeft
        asynchronous: true
        smooth: false
        fillMode: Image.PreserveAspectFit
        autoTransform: true
        onWidthChanged: if(status==Image.Ready) fit()
        onStatusChanged: {
            // update cache source when image is loaded
            if(status === Image.Ready)
                cache.source = source
        }

        // Image cache of the last loaded image
        // Only visible when the main one is loading, to keep an image
        // displayed at all time and smoothen transitions
        Image {
            id: cache

            anchors.fill: parent
            asynchronous: true
            smooth: parent.smooth
            fillMode: parent.fillMode
            autoTransform: parent.autoTransform

            visible: image.status === Image.Loading
        }
    }

    // Busy indicator
    BusyIndicator {
        anchors.centerIn: parent
        // running property binding seems broken, only dynamic binding assignment works
        Component.onCompleted: running = Qt.binding(function() { return image.status === Image.Loading })
    }

    // mouse area
    MouseArea {
        anchors.fill: parent
        property double factor: 1.2
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {
            root.forceActiveFocus();
            if(mouse.button & Qt.MiddleButton)
                drag.target = image // start drag
        }
        onReleased: {
            drag.target = undefined // stop drag
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

    // zoom label
    Label {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 4
        text: (image.status == Image.Ready ? image.scale.toFixed(2) : "1.00") + "x"
        state: "xsmall"
    }
}
