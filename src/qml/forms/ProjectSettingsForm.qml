import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.0

import "../styles"

Item {

    id: root
    property variant model: null // project model
    property int labelWidth: 160

    FileDialog {
        id: fileDialog
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        onAccepted: root.model.url = fileDialog.fileUrl
    }

    GridLayout {
        anchors.fill: parent
        anchors.margins: 30
        columns: 2
        rowSpacing: 10
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "project path"
                color: "white"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            TextField {
                Layout.fillWidth: true
                style: DefaultStyle.textField
                text: (root.model) ? root.model.url : ""
                placeholderText: "/path"
                onEditingFinished: if(root.model) root.model.url = "file://"+text
            }
            ToolButton {
                style: DefaultStyle.largeToolButton
                iconSource: 'qrc:/images/folder_outline.svg'
                onClicked: fileDialog.open();
            }
        }
        Item { // spacer
            Layout.preferredWidth: labelWidth
            Layout.fillHeight: true
        }
    }

}
