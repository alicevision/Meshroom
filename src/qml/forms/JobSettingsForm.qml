import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Item {

    id : root
    property variant model: null // job model
    property int labelWidth: 120

    GridLayout {
        anchors.fill: parent
        anchors.margins: 30
        columns: 2
        rowSpacing: 10
        CustomText {
            text: "user"
            enabled: false
        }
        CustomTextField {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            text: (root.model) ? root.model.user : ""
            enabled: false
            onEditingFinished: if(root.model) root.model.user = text
        }
        CustomText {
            text: "date"
            enabled: false
        }
        CustomTextField {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            text: (root.model) ? root.model.date : ""
            enabled: false
            onEditingFinished: if(root.model) root.model.name = text
        }
        CustomText {
            text: "peak threshold"
        }
        CustomSlider {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            minimumValue: 0.01
            maximumValue: 0.06
            stepSize: 0.01
            value: root.model.peakThreshold
            onValueChanged: if(root.model) root.model.peakThreshold = value;
        }
        CustomText {
            text: "meshing scale"
        }
        CustomSlider {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            minimumValue: 1
            maximumValue: 10
            stepSize: 1
            value: root.model.meshingScale
            onValueChanged: if(root.model) root.model.meshingScale = Math.round(value);
        }
        CustomText {
            text: "initial pair"
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Rectangle {
                height:parent.height
                width: parent.width
                color: _style.window.color.xdarker
                ListView {
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    model: root.model.cameras
                    spacing: 2
                    delegate: Item {
                        property bool selected: false
                        width: parent.width
                        height: childrenRect.height
                        RowLayout {
                            spacing: 20
                            Item {
                                width: 40
                                height: 40*3/4
                                Image {
                                    source: modelData.url
                                    sourceSize.width: parent.width
                                    sourceSize.height: parent.height
                                    asynchronous: true
                                }
                            }
                            CustomText {
                                text: modelData.name
                                color: selected ? _style.text.color.selected : _style.text.color.normal
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
        Item { // spacer
            Layout.preferredWidth: labelWidth
            Layout.fillHeight: true
        }
    }
}
