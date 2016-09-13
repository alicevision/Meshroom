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
        Gallery {
            model: modelData.value
            closeable: false
            onItemAdded: {
                var values = (!modelData.value) ? [] : modelData.value;
                values.push(item.replace("file://", ""));
                currentScene.graph.setNodeAttribute(nodeName, modelData.key, values);
            }
            onItemRemoved: {
                var values = (!modelData.value) ? [] : modelData.value;
                var index = values.indexOf(item.replace("file://",""));
                if(index < 0)
                    return;
                values.splice(index, 1);
                currentScene.graph.setNodeAttribute(nodeName, modelData.key, values);
            }
        }
    }
    Component {
        id: labelDelegate
        Label {
            text: modelData.name
            state: "xsmall"
            enabled: false
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


    Flickable {
        id: flickable
        anchors.fill: parent
        ScrollBar.vertical: ScrollBar {}
        contentWidth: width
        contentHeight: layout.height
        ColumnLayout {
            id: layout
            width: flickable.width - 10
            spacing: 0
            Repeater {
                model: (root.model && root.model.inputs) ? root.model.inputs.count*2 : 0
                delegate: Loader {
                    Layout.fillWidth: true
                    Layout.leftMargin: 2
                    Layout.rightMargin: 2
                    Layout.topMargin: (index%2==0 && index!=0) ? 15 : 0
                    property variant modelData: null
                    property string nodeName: ""
                    sourceComponent: {
                        modelData = root.model.inputs.get(index/2).modelData;
                        nodeName = root.model.name;
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
