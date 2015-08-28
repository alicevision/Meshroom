import QtQuick.Controls 1.3
import QtQuick 2.2
import Popart 0.1

Item {
    anchors.fill: parent
    DropArea {
        anchors.fill: parent
        GLView {
            id: glview
            color: "#333"
            anchors.fill: parent
        }
        onDropped: {
            glview.setPointCloud(drop.urls[0].replace("file://", ""));
        }
    }
}
