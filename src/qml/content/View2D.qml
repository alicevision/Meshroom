import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import ImageGallery 1.0

Rectangle {

    id: root
    color: Style.window.color.xdark

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height*1.333)
        height: Math.min(parent.height, parent.width*0.75)
        color: "transparent"
        border.color: Style.window.color.normal
    }

}
