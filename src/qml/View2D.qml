import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import "controls"

Frame {

    id: root

    // slots
    Keys.onPressed: {
        if(event.key == Qt.Key_F) {
            root.fit();
            event.accepted = true;
        }
    }

    // connections
    Connections {
        target: _window
        onDisplayIn2DView: {
            sourceName.text = attribute.name
            if(!attribute.value) {
                sourceListView.model = 0;
                image.source = "";
                return;
            }
            sourceListView.model = Array.isArray(attribute.value) ? attribute.value : [attribute.value]
            image.source = Qt.resolvedUrl(sourceListView.model[0])
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

    // background
    background: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.2)
    }

    // placeholder, visible when image isn't ready
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height*1.5) * 0.95 // 5% margin
        height: Math.min(parent.height, parent.width*1.5) * 0.95 // 5% margin
        color: "transparent"
        border.color: "#333"
        visible: image.status != Image.Ready
    }

    // image
    Image {
        id: image
        transformOrigin: Item.TopLeft
        asynchronous: true
        smooth: false
        fillMode: Image.PreserveAspectFit
        onWidthChanged: if(status==Image.Ready) fit()
    }

    // busy indicator
    BusyIndicator {
        anchors.centerIn: parent
        running: image.status === Image.Loading
    }

    // mouse area
    MouseArea {
        anchors.fill: parent
        drag.target: image
        property double factor: 1.5
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            root.forceActiveFocus();
            panel.close();
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

    // overlay panel
    SidePanel {
        id: panel
        anchors.fill: parent
        icons: ["qrc:///images/gear.svg", "qrc:///images/input.svg"]
        Flickable {
            anchors.fill: parent
            anchors.margins: 10
            ScrollBar.vertical: ScrollBar {}
            contentWidth: parent.width
            contentHeight: 300
            ColumnLayout {
                anchors.fill: parent
                Label {
                    Layout.fillWidth: true
                    text: "VIEW SETTINGS"
                    state: "small"
                }
                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    columns: 2
                    Label {
                        Layout.fillWidth: true
                        text: "image filtering"
                        state: "xsmall"
                    }
                    CheckBox {
                        Layout.fillWidth: true
                        checked: false
                        text: checked ? "on " : "off"
                        onClicked: image.smooth = checked
                        focusPolicy: Qt.NoFocus
                    }
                    Item { Layout.fillHeight: true } // spacer
                }
            }
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            RowLayout {
                Label {
                    Layout.fillWidth: true
                    text: "VIEW INPUTS"
                    state: "small"
                }
                Label {
                    id: sourceName
                    horizontalAlignment: Text.AlignRight
                    enabled: false
                    state: "small"
                    text: ""
                }
            }
            ListView {
                id: sourceListView
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 1
                delegate: Button {
                    width: ListView.view.width
                    height: 30
                    text: modelData
                    onClicked: image.source = Qt.resolvedUrl(modelData)
                }
            }
        }
    }

    // zoom label
    Label {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 4
        text: image.scale.toFixed(1) + " x"
        state: "xsmall"
    }
}
