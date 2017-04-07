import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.2
import "controls"

Item {

    property Component openScene: FileDialog {
        title: "Open file"
        folder: "/"
        selectExisting: true
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component saveScene: FileDialog {
        title: "Save file"
        folder: "/"
        selectExisting: false
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component openRecentScene: Popup {
        signal accepted(var url)
        signal rejected()
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            Label {
                text: "Recent files"
                enabled: false
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: _application.settings.recentFiles
                ScrollBar.vertical: ScrollBar { active: true }
                delegate: Button {
                    width: parent.width
                    text: modelData.toString().replace("file://", "")
                    onClicked: { accepted(modelData); close(); }
                }
                clip: true
            }
            Button {
                Layout.alignment: Qt.AlignRight
                text: "Clear"
                onClicked: {
                    _application.settings.clearRecentFiles()
                    rejected(); close();
                }
            }
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { rejected(); close(); }
        }
    }
    property Component maySaveScene: Popup {
        signal accepted()
        signal rejected()
        implicitWidth: 250
        implicitHeight: 100
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            Label {
                Layout.fillWidth: true
                maximumLineCount:3
                elide: Text.ElideLeft
                wrapMode: Text.WordWrap
                text: "Do you want to save changes?"
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                Button {
                    text: "Yes"
                    onClicked: { accepted(); close(); }
                }
                Button {
                    text: "No"
                    onClicked: { rejected(); close(); }
                }
                Button {
                    text: "Cancel"
                    onClicked: { close(); }
                }
            }
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { close(); }
        }
    }
    property Component sceneSettings: Popup {
        Flickable {
            anchors.fill: parent
            anchors.margins: 10
            ScrollBar.vertical: ScrollBar {}
            flickableDirection: Flickable.AutoFlickIfNeeded
            contentWidth: parent.width - anchors.margins*2
            contentHeight: 100
            clip: true
            ColumnLayout {
                anchors.fill: parent
                Label {
                    text: "cache folder"
                    state: "small"
                }
                PathField {
                    Layout.fillWidth: true
                    selectFolder: true
                    text: currentScene.cacheUrl.toString().replace("file://", "")
                    onEditingFinished: currentScene.setCacheUrl("file://"+text)
                }
                Item { Layout.fillHeight: true }
            }
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { close(); }
        }
    }
    property Component importTemplate: Popup {
        signal accepted(var url)
        signal rejected()
        ListView {
            anchors.fill: parent
            anchors.margins: 10
            model: _application.templates
            ScrollBar.vertical: ScrollBar { active: true }
            delegate: Button {
                width: parent.width
                text: modelData.name
                onClicked: { accepted(modelData.url); close(); }
            }
            clip: true
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { rejected(); close(); }
        }
    }
    property Component addNode: Popup {
        signal accepted(var selection)
        signal rejected()
        ListView {
            anchors.fill: parent
            anchors.margins: 10
            model: _application.pluginNodes
            ScrollBar.vertical: ScrollBar { active: true }
            delegate: Button {
                width: parent.width
                text: modelData.type
                onClicked: { accepted(modelData.metadata); close(); }
            }
            clip: true
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { rejected(); close(); }
        }
    }
}
