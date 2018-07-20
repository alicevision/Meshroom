import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2

Dialog {
    id: root

    property alias text: textLabel.text
    property alias detailedText: detailedLabel.text
    property alias helperText: helperLabel.text
    property alias icon: iconLabel

    default property alias children: layout.children

    x: parent.width/2 - width/2
    y: parent.height/2 - height/2
    modal: true

    padding: 15
    standardButtons: Dialog.Ok

    RowLayout {
        spacing: 12

        // Icon
        Label {
            id: iconLabel
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            font.family: MaterialIcons.fontFamily
            font.pointSize: 14
            visible: text != ""
        }

        ColumnLayout {
            id: layout
            // Text
            spacing: 12
            Label {
                id: textLabel
                font.bold: true
                visible: text != ""
            }
            // Detailed text
            Label {
                id: detailedLabel
                text: text
                visible: text != ""
            }
            // Additional helper text
            Label {
                id: helperLabel
                visible: text != ""
            }
        }
    }
}
