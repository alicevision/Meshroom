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
            delegate: ProjectDelegate {
                width: GridView.view.cellWidth
                height: GridView.view.cellHeight
            }
        }
        Text {
            text: "Featured projects"
            font.pixelSize: Style.text.size.large
        }
        GridView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: _applicationModel.projects
            cellWidth: 150
            cellHeight: 150
            delegate: ProjectDelegate {
                width: GridView.view.cellWidth
                height: GridView.view.cellHeight
            }
        }
    }
}
