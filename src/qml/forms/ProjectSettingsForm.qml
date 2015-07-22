import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.0

import "../components"

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
        CustomText {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            text: "project path"
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            CustomTextField {
                Layout.fillWidth: true
                text: (root.model) ? root.model.url.toString().replace("file://","") : ""
                placeholderText: "/path"
                onEditingFinished: if(root.model && text) root.model.url = "file://"+text
            }
            CustomToolButton {
                iconSize: _style.icon.size.large
                iconSource: 'qrc:///images/folder_outline.svg'
                onClicked: fileDialog.open();
            }
        }
        Item { // spacer
            Layout.preferredWidth: labelWidth
            Layout.fillHeight: true
        }
    }

}
