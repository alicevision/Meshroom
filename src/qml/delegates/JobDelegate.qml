import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    property bool isSelected: (currentJob.modelData == model.modelData)

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
            anchors.leftMargin: 2
            anchors.rightMargin: 2
            Rectangle {
                Layout.fillWidth: false
                Layout.fillHeight: true
                Layout.preferredWidth: childrenRect.width
                color: Style.window.color.xdark
                Text {
                    anchors.centerIn: parent
                    font.pixelSize: Style.text.size.small
                    color: Style.text.color.dark
                    visible: model.thumbnail == ""
                    text: "N/A"
                }
                Image {
                    anchors.verticalCenter: parent.verticalCenter
                    source: model.thumbnail
                    width: parent.height
                    height: width*3/4.0
                    asynchronous: true
                }
            }
            ColumnLayout {
                Item { Layout.fillHeight: true } // spacer
                Text {
                    Layout.fillWidth: true
                    text: model.name
                    font.pixelSize: Style.text.size.small
                    color: isSelected ? Style.text.color.selected : Style.text.color.normal
                    maximumLineCount: 2
                }
                Text {
                    text: {
                        if(model.status < 0)
                            return "n/a";
                        switch(model.status) {
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
                                return Math.round(model.completion*100)+"%"
                        }
                    }
                    font.pixelSize: Style.text.size.small
                    color: {
                        switch(model.status) {
                            case 6: // PAUSED
                            case 4: // ERROR
                            case 5: // CANCELED
                                return "red";
                            case 0: // BLOCKED
                            case 1: // READY
                            case 2: // RUNNING
                                return "green";
                            case 3: // DONE
                            default:
                                return Style.text.color.dark;
                        }
                    }
                }
                Item { Layout.fillHeight: true } // spacer
            }
        }
    }

}
