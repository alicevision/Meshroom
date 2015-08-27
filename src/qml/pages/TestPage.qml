import QtQuick 2.2
import Popart 0.1

Item {
    anchors.fill: parent
    GLView {
        color: "#333"
        camera: _applicationModel.projects[0].jobs[0].cameras[0]
        anchors.fill: parent
    }
}
