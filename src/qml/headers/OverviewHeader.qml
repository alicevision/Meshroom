import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "../styles"

Item {

    implicitHeight: 60

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
            ToolButton {
                style: DefaultStyle.largeToolButton
                iconSource: 'qrc:/images/add_project.svg'
                tooltip: "add project"
                onClicked: {
                    var newModel = _applicationModel.addNewProject();
                    stackView.push({
                        item: Qt.resolvedUrl("qrc:/pages/NewProjectPage.qml"),
                        properties: { model: newModel }
                    });
                }
            }
        }
    }
}
