import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.Job 0.1

Item {

    property bool isSelected: (currentJob == model.modelData)

    MouseArea {
        id: mouseContainer
        anchors.fill: parent
        hoverEnabled: true
        onClicked: selectJob(index)
        Rectangle {
            anchors.fill: parent
            color: Style.window.color.xdark
            opacity: isSelected ? 0.8 : 0.4
            Behavior on opacity { NumberAnimation {} }
        }
        Rectangle {
            anchors.right: parent.right
            width: 1
            height: parent.height
            color: isSelected ? Style.window.color.selected : Style.window.color.xlight
            visible: (isSelected || mouseContainer.containsMouse)
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            // Rectangle {
            //     Layout.fillWidth: false
            //     Layout.fillHeight: true
            //     Layout.preferredWidth: childrenRect.width
            //     color: Style.window.color.xdark
            //     Text {
            //         anchors.centerIn: parent
            //         font.pixelSize: Style.text.size.small
            //         color: Style.text.color.dark
            //         visible: model.thumbnail == ""
            //         text: "N/A"
            //     }
            //     Image {
            //         anchors.verticalCenter: parent.verticalCenter
            //         source: model.thumbnail
            //         sourceSize: Qt.size(320, 320)
            //         width: parent.height
            //         height: width*3/4.0
            //         asynchronous: true
            //         BusyIndicator {
            //             anchors.centerIn: parent
            //             running: parent.status === Image.Loading
            //         }
            //     }
            // }
            ColumnLayout {
                Item { Layout.fillHeight: true } // spacer
                Text {
                    Layout.fillWidth: true
                    text: model.name
                    font.pixelSize: Style.text.size.small
                    color: Style.text.color.dark
                    // color: isSelected ? Style.text.color.selected : Style.text.color.normal
                }
                Text {
                    Layout.fillWidth: true
                    text: model.date.toLocaleString()
                    font.pixelSize: Style.text.size.small
                    color: isSelected ? Style.text.color.selected : Style.text.color.normal
                    maximumLineCount: 2
                }
                RowLayout {
                    Item { Layout.fillWidth: true } // spacer
                    Text {
                        text: {
                            switch(model.status) {
                            case Job.BLOCKED:
                                return "blocked";
                            case Job.READY:
                                return "ready";
                            case Job.DONE:
                                return "done";
                            case Job.ERROR:
                                return "error";
                            case Job.CANCELED:
                                return "canceled";
                            case Job.PAUSED:
                                return "paused";
                            case Job.NOTSTARTED:
                                return "not started";
                            case Job.SYSTEMERROR:
                                return "n/a";
                            case Job.RUNNING:
                            default:
                                return Math.round(model.completion*100)+"%"
                            }
                        }
                        font.pixelSize: Style.text.size.small
                        color: {
                            switch(model.status) {
                            case Job.PAUSED:
                            case Job.ERROR:
                            case Job.CANCELED:
                            case Job.SYSTEMERROR:
                                return Style.text.color.critical;
                            case Job.BLOCKED:
                            case Job.READY:
                            case Job.RUNNING:
                            case Job.DONE:
                            case Job.NOTSTARTED:
                            default:
                                return Style.text.color.info;
                            }
                        }
                    }
                }
                Item { Layout.fillHeight: true } // spacer
            }
        }
    }

}
