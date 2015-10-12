import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4

import "../components"

Item {

    id: root

    implicitWidth: 200
    implicitHeight: 60

    Component.onCompleted: {
        if(index==0) {
            currentProject = projectModel;
            currentJob = model;
        }
    }

    MouseArea {
        id: mouseContainer
        anchors.fill: parent
        anchors.margins: 2
        hoverEnabled: true
        onClicked: {
            currentProject = projectModel;
            currentJob = model;
        }
        Rectangle { // background
            anchors.fill: parent
            color: _style.window.color.xdarker
            opacity: mouseContainer.containsMouse ? 0.5 : 0
            Behavior on opacity { NumberAnimation {} }
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
                Image {
                    anchors.verticalCenter: parent.verticalCenter
                    source: model.thumbnail
                    width: parent.height
                    height: width*3/4.0
                    asynchronous: true
                }
            }
            ColumnLayout {
                CustomTextField {
                    Layout.fillWidth: true
                    text: model.name
                    textSize: _style.text.size.normal
                    color: (currentJob == model) ? _style.text.color.selected : _style.text.color.normal
                    state: "HIDDEN"
                    onEditingFinished: model.name = text
                }
                RowLayout {
                    CustomText {
                        text: model.images.count+ " images"
                        textSize: _style.text.size.small
                        color: _style.text.color.darker
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    CustomText {
                        text: {
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
                                    return Math.round(completion*100)+"%"
                            }
                        }
                        textSize: _style.text.size.small
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
                                    return _style.text.color.darker;
                            }
                        }
                    }
                }
            }
            Item {
                Layout.fillWidth: true
            }
        }
    }
}
