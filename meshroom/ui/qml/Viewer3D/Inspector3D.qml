import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

FloatingPane {
    id: root

    implicitWidth: 200
    padding: 0

    MouseArea {
        anchors.fill: parent
        onWheel: function(wheel) {
            wheel.accepted = true
        }
    }
}
