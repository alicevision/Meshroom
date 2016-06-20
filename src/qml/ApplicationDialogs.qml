import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2
import DarkStyle.Controls 1.0
import DarkStyle.Dialogs 1.0
import DarkStyle 1.0
import "delegates"

Item {

    property Component openScene: FileDialog {
        title: "Please select a meshroom file"
        folder: "/"
        selectExisting: true
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component saveScene: FileDialog {
        title: "Please select a meshroom file"
        folder: "/"
        selectExisting: false
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component maySaveScene: Dialog {
        title: "Save?"
        content: RowLayout {
            Button {
                Layout.fillWidth: true
                text: "No"
                onClicked: reject()
            }
            Button {
                Layout.fillWidth: true
                text: "Yes"
                onClicked: accept()
            }
        }
    }
    property Component addNode: Dialog {
        property variant selection: ""
        title: "New node"
        content: ColumnLayout {
            spacing: 0
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: _application.pluginNodes
                delegate: Rectangle {
                    width: parent.width
                    height: 30
                    color: mouseArea.containsMouse ? "transparent" : Style.window.color.xdark
                    border.color: Style.window.color.dark
                    Behavior on color { ColorAnimation {}}
                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            selection = modelData.metadata;
                            accept();
                        }
                    }
                    Text {
                        id: txt
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        text: modelData.plugin + "/" + modelData.type
                        color: mouseArea.containsMouse ? Style.text.color.selected : Style.text.color.normal
                        Behavior on color { ColorAnimation {}}
                    }
                }
            }
            Button {
                Layout.fillWidth: true
                text: "Cancel"
                onClicked: reject()
            }
        }
    }
}
