import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root

    width: parent.width
    height: childrenRect.height

    property variant modelData: model
    property Component sliderControl: Slider {
        // minimumValue: modelData.min
        Component.onCompleted: minimumValue = modelData.min // workaround
        maximumValue: modelData.max
        stepSize: modelData.step
        value: modelData.value
        onValueChanged: modelData.value = value
        updateValueWhileDragging: true
    }
    property Component textControl: TextField {
        text: modelData.value
        onEditingFinished: modelData.value = text
    }
    property Component comboControl: ComboBox {
        model: modelData.options
        onActivated: {
            modelData.value = textAt(index);
            currentIndex = index;
        }
        Component.onCompleted: currentIndex = find(modelData.value)
    }
    property Component pairControl: Item {
        width: parent.width
        height: childrenRect.height
        function setPairA(url) {
            var items = modelData.value;
            items[0] = url.replace("file://", "");
            modelData.value = items;
        }
        function setPairB(url) {
            var items = modelData.value;
            items[1] = url.replace("file://", "");
            modelData.value = items;
        }
        RowLayout {
            width: parent.width
            height: childrenRect.height
            Rectangle {
                Layout.preferredHeight: 80
                Layout.preferredWidth: 80*4/3.0
                color: "black"
                Image {
                    anchors.fill: parent
                    source: modelData.value[0]
                    sourceSize: Qt.size(320, 320)
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    ToolButton {
                        anchors.fill: parent
                        text: "select"
                        iconSource: "qrc:///images/disk.svg"
                        onClicked: openImageSelectionDialog(setPairA)
                    }
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: parent.status === Image.Loading
                    }
                }
            }
            Rectangle {
                Layout.preferredHeight: 80
                Layout.preferredWidth: 80*4/3.0
                color: "black"
                Image {
                    anchors.fill: parent
                    source: modelData.value[1]
                    sourceSize: Qt.size(320, 320)
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    ToolButton {
                        anchors.fill: parent
                        text: "select"
                        iconSource: "qrc:///images/disk.svg"
                        onClicked: openImageSelectionDialog(setPairB)
                    }
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: parent.status === Image.Loading
                    }
                }
            }
            Item {
                Layout.fillWidth: true
            }
        }
    }

    RowLayout {
        width: parent.width
        height: childrenRect.height
        Item {
            Layout.preferredWidth: 120
            Layout.preferredHeight: attributeLoader.height
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: modelData.name
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            Loader {
                id: attributeLoader
                width: parent.width
                height: item.height
                property variant modelData: model
                sourceComponent: {
                    switch(modelData.type){
                        case 0: return textControl
                        case 1: return sliderControl
                        case 2: return comboControl
                        case 3: return pairControl
                    }
                }
            }
        }
    }
}
