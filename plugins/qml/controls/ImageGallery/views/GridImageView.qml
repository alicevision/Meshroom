import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 60

    // gridview
    GridView {
        id: gridview
        anchors.fill: parent
        anchors.margins: 2
        ScrollBar.vertical: ScrollBar {}
        cellWidth: root.thumbnailSize
        cellHeight: root.thumbnailSize
        model: visualModel.parts.grid
        clip: true
    }
}
