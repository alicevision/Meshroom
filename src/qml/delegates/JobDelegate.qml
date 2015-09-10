import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import Popart 0.1

import "../components"


Item {

    id: root
    property variant jobModel: modelData

    implicitWidth: 200
    implicitHeight: 60

    MouseArea {
        id: mouseContainer
        anchors.fill: parent
        anchors.margins: 2
        hoverEnabled: true
        onClicked: jobModel.select()
        Rectangle { // background
            anchors.fill: parent
            color: _style.window.color.xdarker
            opacity: (mouseContainer.containsMouse || modelData==_applicationModel.currentProject.currentJob)? 0.5:0
            Behavior on opacity { NumberAnimation {} }
        }
        Rectangle { // status bar
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 2
            width: 3
            radius: 2
            height: parent.height * 0.8
            color: {
                switch(jobModel.status) {
                    case 6: // PAUSED
                    case 4: // ERROR
                    case 5: // CANCELED
                        return "red";
                    case 0: // BLOCKED
                    case 1: // READY
                    case 2: // RUNNING
                    case 3: // DONE
                    default:
                        return "transparent";
                }
            }
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
                    source: (jobModel.cameras.length > 0) ? jobModel.cameras[0].url : ""
                    width: parent.height
                    height: width*3/4.0
                    asynchronous: true
                }
            }
            ColumnLayout {
                CustomText {
                    text: jobModel.date
                    textSize: _style.text.size.normal
                    color: (_applicationModel.currentProject
                        && _applicationModel.currentProject.currentJob == jobModel)?_style.text.color.selected:_style.text.color.normal
                }
                RowLayout {
                    CustomText {
                        text: jobModel.cameras.length+ " images"
                        textSize: _style.text.size.small
                        color: _style.text.color.darker
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    CustomText {
                        text: {
                            switch(jobModel.status) {
                                case 6: // PAUSED
                                    return "PAUSED";
                                case 4: // ERROR
                                    return "ERROR";
                                case 5: // CANCELED
                                    return "CANCELED";
                                case 3: // DONE
                                    return "DONE"
                                case 0: // BLOCKED
                                case 1: // READY
                                case 2: // RUNNING
                                default:
                                    return Math.round(jobModel.completion*100)+"%"
                            }
                        }
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
