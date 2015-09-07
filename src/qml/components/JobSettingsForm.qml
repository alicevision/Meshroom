import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Item {

    id : root
    property variant jobModel: null
    property int labelWidth: 100

    GridLayout {
        anchors.fill: parent
        anchors.margins: 10
        columns: 2
        rowSpacing: 10
        CustomText {
            text: "quality"
        }
        CustomComboBox {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
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
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "A"
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
                }
            }
            ResourceDropArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "B"
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
                }
            }
        }
        Item { // spacer
            Layout.preferredWidth: labelWidth
        }
    }
}
