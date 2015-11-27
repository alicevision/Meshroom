import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4

Item {
    property Component background: Item {}
    property Component header: Item {}
    property Component bodyA: Item {}
    property Component bodyB: Item {}

    Loader { // background
        anchors.fill: parent
        sourceComponent: background
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Loader { // header
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: item.height
            sourceComponent: header
        }
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Loader { // left
                width: 230
                sourceComponent: bodyA
            }
            Loader { // right
                Layout.minimumWidth: 50
                Layout.fillWidth: true
                sourceComponent: bodyB
            }
            orientation: Qt.Horizontal
            handleDelegate: Rectangle {
                width: 2
                height: 2
                color: "#111"
            }
        }
    }
}
