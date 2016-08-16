import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0
import ImageGallery 1.0

Item {

    id : root

    // properties
    property variant model: null
    clip: true

    // signal / slots
    onModelChanged: {
        stackView.pop();
        if(!root.model)
            return;
        loadAlembic("");
        var outputs = root.model.outputs;
        if(outputs.count > 0) {
            for(var i=0; i < outputs.count; ++i) {
                if(outputs.get(i).type == Attribute.OBJECT3D)
                    loadAlembic(currentScene.graph.getNodeAttribute(root.model.name, outputs.get(i).name));
            }
        }
    }

    // attribute delegates
    Component {
        id: emptyDelegate
        Item {}
    }
    Component {
        id: imageListDelegate
        RowLayout {
            Label {
                text: (modelData && Array.isArray(modelData.value)) ? modelData.value.length + " items" : "0 item"
            }
            Item { Layout.fillWidth: true } // spacer
            ToolButton {
                // iconSource: "qrc:///images/arrow.svg"
                onClicked: stackView.push(galleryTab, {
                    node: nodeName,
                    attribute: modelData,
                    model: modelData.value
                })
            }
        }
    }
    Component {
        id: labelDelegate
        Label {
            text: modelData.name
            state: "xsmall"
        }
    }
    Component {
        id: sliderDelegate
        Slider {
            Component.onCompleted: {
                from = modelData.min;
                to = modelData.max;
                stepSize = modelData.step;
                value = modelData.value;
            }
            onValueChanged: currentScene.graph.setNodeAttribute(nodeName, modelData.key, value)
        }
    }
    Component {
        id: textfieldDelegate
        TextField {
            text: (modelData && modelData.value) ? modelData.value : ""
            onEditingFinished: currentScene.graph.setNodeAttribute(nodeName, modelData.key, text)
        }
    }
    Component {
        id: comboboxDelegate
        ComboBox {
            Component.onCompleted: currentIndex = find(modelData.value)
            model: modelData.options
            onActivated: currentScene.graph.setNodeAttribute(nodeName, modelData.key, textAt(index))
        }
    }
    Component {
        id: checkboxDelegate
        CheckBox {
            Component.onCompleted: checked = modelData.value
            onClicked: currentScene.graph.setNodeAttribute(nodeName, modelData.key, checked)
        }
    }

    // stack view components
    Component {
        id: mainPropertiesTab
        Flickable {
            id: flickable
            ScrollBar.vertical: ScrollBar {}
            contentWidth: stackView.width
            contentHeight: grid.height
            GridLayout {
                id: grid
                width: flickable.width - 10
                columns: 2
                rowSpacing: 0
                columnSpacing: 2
                Repeater {
                    model: (root.model && root.model.inputs) ? root.model.inputs.count*2 : 0
                    delegate: Loader {
                        Layout.fillWidth: index%2 != 0
                        Layout.preferredWidth: index%2 ? parent.width : parent.width*0.3
                        Layout.margins: 5
                        property variant modelData: null
                        property string nodeName: ""
                        clip: true
                        sourceComponent: {
                            modelData = root.model.inputs.get(index/2).modelData;
                            nodeName = root.model.name;
                            if(modelData.type == Attribute.UNKNOWN)
                                return emptyDelegate
                            if(index % 2 == 0)
                                return labelDelegate;
                            switch(modelData.type) {
                                case Attribute.UNKNOWN: return emptyDelegate
                                case Attribute.TEXTFIELD: return textfieldDelegate
                                case Attribute.SLIDER: return sliderDelegate
                                case Attribute.COMBOBOX: return comboboxDelegate
                                case Attribute.CHECKBOX: return checkboxDelegate
                                case Attribute.IMAGELIST: return imageListDelegate
                                case Attribute.OBJECT3D: return emptyDelegate
                            }
                        }
                    }
                }
            }
        }
    }
    Component {
        id: galleryTab
        Gallery {
            property variant node: null
            property variant attribute: null
            closeable: true
            onClosed: stackView.pop()
            onItemAdded: {
                var values = attribute.value;
                values.push(item.replace("file://", ""));
                currentScene.graph.setNodeAttribute(node, attribute.key, values);
                model = attribute.value; // force model update
            }
            onItemRemoved: {
                var values = attribute.value;
                var index = values.indexOf(item.replace("file://",""));
                if (index < 0)
                    return;
                values.splice(index, 1);
                currentScene.graph.setNodeAttribute(node, attribute.key, values);
                model = attribute.value; // force model update
            }
        }
    }

    // stack view
    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: mainPropertiesTab
    }
}
