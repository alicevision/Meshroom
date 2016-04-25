import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Logger 1.0
import NodeEditor 1.0
import "content"

ColumnLayout {
    id: root
    spacing: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Header {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
        }
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            SplitView {
                width: parent.width * 0.75
                Item { // views
                    height: parent.height * 0.6
                    Rectangle { // tab background
                        height: 20
                        width: parent.width
                        color: Style.window.color.xdark
                    }
                    TabView {
                        anchors.fill: parent
                        currentIndex: 1
                        Tab {
                            title: "2D"
                            View2D {
                                anchors.fill: parent
                            }
                        }
                        Tab {
                            title: "3D"
                            View3D {
                                anchors.fill: parent
                            }
                        }
                    }
                }
                NodeEditor {
                    Layout.fillHeight: true
                    onSelectionChanged: scenesettings.model = node
                }
                orientation: Qt.Vertical
            }
            Settings {
                id: scenesettings
                Layout.fillWidth: true
            }
            orientation: Qt.Horizontal
        }
    }
    LogBar {
        property bool expanded: false
        Layout.fillWidth: true
        Layout.preferredHeight: expanded ? parent.height/3 : 30
        Behavior on Layout.preferredHeight { NumberAnimation {}}
        color: Style.window.color.xdark
        onToggle: expanded = !expanded
    }
}
