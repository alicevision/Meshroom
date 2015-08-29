import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import Popart 0.1

import "../components"


Item {
    id: root
    implicitWidth: 200
    implicitHeight: 60
    MouseArea {
        id: mouseContainer
        anchors.fill: parent
        anchors.margins: 2
        hoverEnabled: true
        onClicked: jobSelected(projectID, index)
        Rectangle { // background
            anchors.fill: parent
            color: mouseContainer.containsMouse ? _style.window.color.xdarker : _style.window.color.darker
            Behavior on color { ColorAnimation {} }
        }
        Rectangle { // status bar
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 2
            width: 3
            radius: 2
            height: parent.height * 0.8
            color: (index%3==0)?"red":"transparent"
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 6
            spacing: 10
            Behavior on opacity { NumberAnimation {} }
            Rectangle { // job thumbnail
                Layout.fillWidth: false
                Layout.fillHeight: true
                Layout.preferredWidth: childrenRect.width
                color: _style.window.color.xdarker
                MouseArea {
                    id: thumbnailMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                }
                Image {
                    anchors.verticalCenter: parent.verticalCenter
                    source: (modelData.cameras.length > 0) ? modelData.cameras[0].url : ""
                    width: parent.height
                    height: width*3/4.0
                    asynchronous: true
                }
            }
            ColumnLayout {
                CustomText {
                    text: modelData.date
                    textSize: _style.text.size.normal
                    color: isCurrentJob(projectID, index)?_style.text.color.selected:_style.text.color.normal
                }
                RowLayout {
                    CustomText {
                        text: modelData.cameras.length+ " images"
                        textSize: _style.text.size.small
                        color: _style.text.color.darker
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    CustomText {
                        text: "N%"
                        textSize: _style.text.size.small
                        color: _style.text.color.darker
                    }
                }
            }
            Item {
                Layout.fillWidth: true
            }
        }
    }
}
