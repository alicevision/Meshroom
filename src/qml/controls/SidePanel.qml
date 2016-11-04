import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0

Item {

    id: root
    property real maxWidthRatio: 0.4
    property variant icons: []
    property color backgroundColor: Qt.rgba(0, 0, 0, 0.5)

    function open() {
        panel.Layout.minimumWidth = parent.width * maxWidthRatio
    }
    function close() {
        panel.Layout.minimumWidth = 0
    }
    function toggle() {
        isOpened() ? close() : open()
    }
    function isOpened() {
        return (panel.Layout.minimumWidth != 0);
    }

    Component.onCompleted: {
        while(root.children.length > 1) {
            root.children[1].visible = false;
            root.children[1].parent = panel;
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: -1
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        Rectangle {
            id: panel
            color: root.backgroundColor
            clip: true
            Layout.fillHeight: true
            Behavior on Layout.minimumWidth { NumberAnimation {}}
        }
        Rectangle {
            Layout.preferredWidth: 30
            Layout.alignment: Qt.AlignTop
            Layout.fillHeight: true
            color: root.backgroundColor
            ListView {
                width: parent.width
                height: model.length*30
                orientation: ListView.Vertical
                model: root.icons
                interactive: false
                spacing: 0
                delegate: ToolButton {
                    icon: modelData
                    enabled: (panel.children.length > index)? panel.children[index].enabled : false
                    onClicked: {
                        for(var i=0; i < panel.children.length; ++i)
                            panel.children[i].visible = false;
                        panel.children[index].visible = true;
                        root.open()
                    }
                }
            }
        }
    }
}
