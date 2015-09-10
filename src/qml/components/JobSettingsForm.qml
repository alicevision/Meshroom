import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Item {

    id : root
    property variant jobModel: null
    property bool enabled: (jobModel.status < 0)
    property int labelWidth: 100

    GridLayout {
        anchors.fill: parent
        anchors.margins: 10
        columns: 2
        CustomText {
            text: "quality"
        }
        CustomComboBox {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            enabled: root.enabled
            model: ["NORMAL", "HIGH", "ULTRA"]
            currentIndex: (root.jobModel)? root.jobModel.describerPreset : 1
            onCurrentIndexChanged: if(root.jobModel) root.jobModel.describerPreset = currentIndex;
        }
        CustomText {
            text: "meshing scale"
        }
        CustomSlider {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            enabled: root.enabled
            minimumValue: 1
            maximumValue: 10
            stepSize: 1
            value: root.jobModel.meshingScale
            onValueChanged: if(root.jobModel) root.jobModel.meshingScale = Math.round(value);
        }
        CustomText {
            text: "initial pair"
        }
        RowLayout {
            ResourceDropArea {
                Layout.preferredWidth: 150
                Layout.preferredHeight: Layout.preferredWidth*2/3
                title: "A"
                enabled: root.enabled
                onFilesDropped: root.jobModel.setPairA(files[0])
                Rectangle {
                    anchors.fill: parent
                    visible: (root.jobModel.pairA!=null)
                    opacity: 0.3
                    color: "black"
                }
                Image {
                    anchors.fill: parent
                    source: root.jobModel.pairA
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    Rectangle { // state indicator (enabled or not)
                        anchors.fill: parent
                        visible: !root.enabled
                        color: "#99000000"
                    }
                }
            }
            ResourceDropArea {
                Layout.preferredWidth: 150
                Layout.preferredHeight: Layout.preferredWidth*2/3
                title: "B"
                enabled: root.enabled
                onFilesDropped: root.jobModel.setPairB(files[0])
                Rectangle {
                    anchors.fill: parent
                    visible: (root.jobModel.pairB!=null)
                    opacity: 0.3
                    color: "black"
                }
                Image {
                    anchors.fill: parent
                    source: root.jobModel.pairB
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    Rectangle { // state indicator (enabled or not)
                        anchors.fill: parent
                        visible: !root.enabled
                        color: "#99000000"
                    }
                }
            }
            Item { // spacer
                Layout.fillWidth: true
            }
        }
        Item { // spacer
            Layout.preferredWidth: labelWidth
            Layout.fillHeight: true
        }
    }
}
