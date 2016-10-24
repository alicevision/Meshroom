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
                if(outputs.data(outputs.index(i,0), AttributeCollection.TypeRole) == Attribute.OBJECT3D)
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
                var values = modelData.value ? modelData.value : []
                if(!Array.isArray(values))
                    values = [modelData.value]
                values.push(item.replace("file://", ""));
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = values; // change value
                currentScene.graph.setAttribute(o)
            }
            onItemRemoved: {
                var values = modelData.value ? modelData.value : []
                if(!Array.isArray(values))
                    values = [modelData.value]
                var index = values.indexOf(item.replace("file://",""));
                if(index < 0)
                    return;
                values.splice(index, 1);
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = values; // change value
                currentScene.graph.setAttribute(o)
            }
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
            onValueChanged: {
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = value; // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: textfieldDelegate
        TextField {
            text: (modelData && modelData.value) ? modelData.value : ""
            onEditingFinished: {
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = text; // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: comboboxDelegate
        ComboBox {
            Component.onCompleted: currentIndex = find(modelData.value)
            model: modelData.options
            onActivated: {
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = textAt(index); // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: checkboxDelegate
        CheckBox {
            Component.onCompleted: checked = modelData.value
            onClicked: {
                var o = modelData.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = checked; // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }


    ListView {
        anchors.fill: parent
        ScrollBar.vertical: ScrollBar {}
        model: (root.model && root.model.inputs) ? root.model.inputs : 0
        spacing: 20
        delegate: ColumnLayout {
            width: ListView.view.width
            Label {
                Layout.fillWidth: true
                text: model.name
                enabled: false
                state: "small"
            }
            Loader {
                Layout.fillWidth: true
                property variant modelData: null
                property string nodeName: ""
                sourceComponent: {
                    modelData = model.modelData;
                    nodeName = root.model.name;
                    switch(model.type) {
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
