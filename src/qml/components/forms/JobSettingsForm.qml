import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../../styles"

Item {

    id : root
    property variant model: null // job model
    property int labelWidth: 160

    GridLayout {
        anchors.fill: parent
        anchors.margins: 30

        columns: 2
        rowSpacing: 10
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "user"
                color: "#666"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            TextField {
                width: parent.width
                style: DefaultStyle.textField
                text: (root.model) ? root.model.user : ""
                placeholderText: ""
                enabled: false
                onEditingFinished: if(root.model) root.model.user = text
            }
        }
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "date"
                color: "#666"
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            TextField {
                width: parent.width
                style: DefaultStyle.textField
                text: (root.model) ? root.model.date : ""
                placeholderText: ""
                enabled: false
                onEditingFinished: if(root.model) root.model.name = text
            }
        }
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "peak threshold"
                color: "white"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            Slider {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                style: DefaultStyle.slider
                minimumValue: 0.01
                maximumValue: 0.06
                stepSize: 0.01
                value: root.model.peakThreshold
                onValueChanged: if(root.model) root.model.peakThreshold = value;
            }
        }
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "meshing scale"
                color: "white"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            Slider {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width
                style: DefaultStyle.slider
                minimumValue: 1
                maximumValue: 10
                stepSize: 1
                value: root.model.meshingScale
                onValueChanged: if(root.model) root.model.meshingScale = Math.round(value);
            }
        }
        Item {
            Layout.preferredWidth: labelWidth
            Layout.preferredHeight: childrenRect.height
            Text {
                text: "initial pair"
                color: "white"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 1
                font.pointSize: 12
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Rectangle {
                height:parent.height
                width: parent.width
                color: "#111"
                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: root.model.cameras
                    spacing: 2
                    delegate: Rectangle {
                        property bool selected: false
                        width: parent.width
                        height: childrenRect.height
                        color: selected ? "#5BB1F7" : "#000"
                        RowLayout {
                            spacing: 20
                            Rectangle {
                                width: 60
                                height: 60*3/4
                                color: "#222"
                                Image {
                                    source: modelData.url
                                    sourceSize.width: parent.width
                                    sourceSize.height: parent.height
                                    asynchronous: true
                                }
                            }
                            Text {
                                text: modelData.name
                                color: "white"
                                font.pointSize: 11
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if(root.model.removePairElement(modelData.url)) {
                                    selected = false;
                                    return;
                                }
                                if(root.model.addPairElement(modelData.url))
                                    selected = true;
                            }
                        }
                    }
                }
                Text {
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    text: root.model.pair.length+"/2"
                    color: "white"
                    font.pointSize: 12
                }
            }
        }
        // Item {
        //     Layout.preferredWidth: labelWidth
        //     Layout.preferredHeight: childrenRect.height
        //     Text {
        //         text: "user note"
        //         color: "white"
        //         anchors.verticalCenter: parent.verticalCenter
        //         elide: Text.ElideRight
        //         wrapMode: Text.WrapAnywhere
        //         maximumLineCount: 1
        //         font.pointSize: 12
        //     }
        // }
        // Item {
        //     Layout.fillWidth: true
        //     Layout.preferredHeight: childrenRect.height
        //     TextArea {
        //         anchors.verticalCenter: parent.verticalCenter
        //         width: parent.width
        //         style: DefaultStyle.textArea
        //         text: ""
        //         onTextChanged: root.model.note = text;
        //     }
        // }
        Item { // spacer
            Layout.preferredWidth: labelWidth
            Layout.fillHeight: true
        }
    }
}
