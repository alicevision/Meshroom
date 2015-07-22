import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "../components"

Rectangle {

    implicitHeight: 60
    color: _style.window.color.darker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        spacing: 20
        Item { // spacer
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        RowLayout {
            Layout.fillWidth: false
            Layout.preferredWidth: childrenRect.width
            spacing: 0
            CustomToolButton {
                iconSource: 'qrc:///images/add_project.svg'
                tooltip: "add project"
                onClicked: {
                    var newModel = _applicationModel.addNewProject();
                    stackView.push({
                        item: Qt.resolvedUrl("../pages/NewProjectPage.qml"),
                        properties: { model: newModel }
                    });
                }
            }
        }
    }
}
