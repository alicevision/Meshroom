import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4

import "../components"

Item {

    id : root

    property Component sliderControl: CustomSlider {
        onValueChanged: modelData.value = value
        value: modelData.value
        minimumValue: modelData.min
        maximumValue: modelData.max
        stepSize: modelData.step
        // tickmarksEnabled: true
        updateValueWhileDragging: true
    }
    property Component textControl: CustomTextField {
        text: modelData.value
        onEditingFinished: modelData.value = text
    }
    property Component comboControl: CustomComboBox {
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
        RowLayout {
            width: parent.width
            height: childrenRect.height
            ResourceDropArea {
                Layout.preferredWidth: 100
                Layout.preferredHeight: 100
                title: "A"
                onFilesDropped: {
                    var items = modelData.value;
                    items[0] = files[0].replace("file://", "");
                    modelData.value = items;
                }
                Image {
                    anchors.fill: parent
                    sourceSize.width: 256
                    sourceSize.height: 256
                    source: (modelData.value.length>0)?modelData.value[0]:""
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
                Layout.preferredWidth: 100
                Layout.preferredHeight: 100
                title: "B"
                onFilesDropped: {
                    var items = modelData.value;
                    items[1] = files[0].replace("file://", "");
                    modelData.value = items;
                }
                Image {
                    anchors.fill: parent
                    sourceSize.width: 256
                    sourceSize.height: 256
                    source: (modelData.value.length>1)?modelData.value[1]:""
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    Rectangle { // state indicator (enabled or not)
                        anchors.fill: parent
                        visible: !root.enabled
                        color: "#99000000"
                    }
                }
            }
            Item {
                Layout.fillWidth: true
            }
        }
    }

    CustomScrollView {
        anchors.fill: parent
        anchors.margins: 10
        verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn
        ListView {
            model: currentJob.steps
            spacing: 5
            interactive: false
            delegate: ColumnLayout {
                property variant modelData: model
                width: parent.width
                height: childrenRect.height
                // spacing: 20
                // CustomText {
                //     width: parent.width
                //     height: childrenRect.height
                //     text: modelData.name
                //     textSize: _style.text.size.large
                // }
                ListView {
                    interactive: false
                    spacing: 5
                    Layout.fillWidth: true
                    height: childrenRect.height
                    model: modelData.attributes
                    delegate: Item {
                        property variant modelData: model
                        width: parent.width
                        height: childrenRect.height
                        RowLayout {
                            width: parent.width
                            height: childrenRect.height
                            Item {
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: attributeLoader.height
                                CustomText {
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
                }
            }
        }
    }
}
