import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Item {

    id : root
    property variant jobModel: null
    property int labelWidth: 120

    GridLayout {
        anchors.fill: parent
        anchors.margins: 20
        columns: 2
        rowSpacing: 5
        CustomText {
            text: "peak threshold"
        }
        CustomSlider {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            minimumValue: 0.01
            maximumValue: 0.06
            stepSize: 0.01
            value: root.jobModel.peakThreshold
            onValueChanged: if(root.jobModel) root.jobModel.peakThreshold = value;
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
            }
            ResourceDropArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                title: "B"
            }
        }
        Item { // spacer
            Layout.preferredWidth: labelWidth
        }
    }
}
