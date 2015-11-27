import QtQuick 2.5
import QtQuick.Layouts 1.2

Item {

    id: root
    property Component background: Item {}
    property Component header: Item {}
    property Component body: Item {}

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
        Loader { // body
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: body
        }
    }
}
