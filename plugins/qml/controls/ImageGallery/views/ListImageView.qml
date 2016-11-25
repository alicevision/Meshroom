import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 60

    // listview
    ListView {
        id: listview
        property alias cellHeight: root.thumbnailSize
        anchors.fill: parent
        anchors.margins: 2
        ScrollBar.vertical: ScrollBar {}
        model: visualModel.parts.list
        spacing: 4
        clip: true
    }
}
