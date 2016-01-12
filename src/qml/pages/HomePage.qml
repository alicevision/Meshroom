import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "../delegates"

Rectangle {

    color: Style.window.color.normal

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        // MouseArea {
        //     Image {
        //         text: "Open new location..."
        //         onClicked: openProjectDialog()
        //         source: "qrc:///images/plus.svg"
        //     }
        //
        // }

        // MouseArea {
        //     Layout.preferredWidth: 300
        //     Layout.preferredHeight: 50
        //     onClicked: openProjectDialog()
        //     Rectangle {
        //         anchors.fill: parent
        //         anchors.margins: 5
        //         color: Style.window.color.xdark
        //         RowLayout {
        //             anchors.centerIn: parent
        //             Image {
        //                 sourceSize: Qt.size(25, 25)
        //                 source: "qrc:///images/plus.svg"
        //             }
        //             Text {
        //                 text: "Open new location..."
        //             }
        //         }
        //     }
        // }

        Button {
            text: "Open new location..."
            iconSource: "qrc:///images/plus.svg"
            onClicked: openProjectDialog()
        }
        GridView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: _applicationModel.projects
            cellWidth: 150
            cellHeight: 150
            // clip: true
            delegate: ProjectDelegate {
                width: GridView.view.cellWidth
                height: GridView.view.cellHeight
            }
        }
    }
}
