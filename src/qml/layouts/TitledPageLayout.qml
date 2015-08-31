import QtQuick 2.2
import QtQuick.Layouts 1.1

Item {
    property Component background: Item {}
    property Component header: Item {}
    property Component body: Item {}

    // background
    Loader {
        anchors.fill: parent
        sourceComponent: background
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // header
        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: item.height
            sourceComponent: header
        }

        // body
        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: body
        }
    }
}
