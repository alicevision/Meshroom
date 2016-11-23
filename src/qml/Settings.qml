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

    // attribute delegates
    Component {
        id: emptyDelegate
        Item {}
    }
    Component {
        id: imageListDelegate
        Gallery {
            model: attribute.isConnected ? connectedAttribute.value : attribute.value
            enabled: !attribute.isConnected
            gridIcon: "qrc:///images/grid.svg"
            listIcon: "qrc:///images/list.svg"
            background: Rectangle {
                color: "#5BB1F7"
                Image {
                    anchors.fill: parent
                    source: "qrc:///images/stripes.png"
                    fillMode: Image.Tile
                    opacity: 0.5
                }
            }
            onItemAdded: {
                if(attribute.isConnected)
                    return;
                var values = attribute.value ? attribute.value : []
                if(!Array.isArray(values))
                    values = [attribute.value]
                for(var i=0; i<urls.length; ++i)
                    values.push(urls[i].replace("file://", ""));
                var o = attribute.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = values; // change value
                currentScene.graph.setAttribute(o)

            }
            onItemRemoved: {
                if(attribute.isConnected)
                    return;
                var values = attribute.value ? attribute.value : []
                if(!Array.isArray(values))
                    values = [attribute.value]
                for(var i=0; i<urls.length; ++i) {
                    var index = values.indexOf(urls[i].replace("file://",""));
                    if(index < 0)
                        return;
                    values.splice(index, 1);
                }
                var o = attribute.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = values; // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: sliderDelegate
        Slider {
            id: slider
            enabled: !attribute.isConnected
            from: attribute.min
            to: attribute.max
            stepSize: attribute.step
            value: attribute.isConnected ? connectedAttribute.value : attribute.value
            onPressedChanged: {
                if(pressed || value == attribute.value || attribute.isConnected)
                    return
                var o = attribute.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = value; // change value
                currentScene.graph.setAttribute(o)
            }
            ToolTip {
                parent: slider.handle
                visible: slider.pressed
                text: {
                    var value = (slider.from + (slider.to-slider.from) * slider.position);
                    return value.toFixed(2)
                }
            }
        }
    }
    Component {
        id: textfieldDelegate
        TextField {
            enabled: !attribute.isConnected
            text: {
                var v = attribute.isConnected ? connectedAttribute.value : attribute.value
                return Array.isArray(v) ? "[Array]" : v;
            }
            selectByMouse: true
            onEditingFinished: {
                focus = false
                if(attribute.isConnected || text == attribute.value)
                    return
                var o = attribute.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = text; // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: comboboxDelegate
        ComboBox {
            enabled: !attribute.isConnected
            model: attribute.options
            Component.onCompleted: {
                currentIndex = Qt.binding(function() {
                    return find(attribute.isConnected ? connectedAttribute.value : attribute.value)
                })
            }
            onActivated: {
                if(attribute.isConnected)
                    return;
                var o = attribute.serializeToJSON()
                o['node'] = nodeName; // add a reference to the node
                o['value'] = textAt(index); // change value
                currentScene.graph.setAttribute(o)
            }
        }
    }
    Component {
        id: checkboxDelegate
        CheckBox {
            enabled: !attribute.isConnected
            Component.onCompleted: checked = attribute.isConnected ? connectedAttribute.value : attribute.value
            onClicked: {
                if(attribute.isConnected)
                    return;
                var o = attribute.serializeToJSON()
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
                horizontalAlignment: Text.AlignRight
                state: "small"
            }
            Loader {
                Layout.fillWidth: true
                property string nodeName: ""
                property variant attribute: null
                property variant connectedAttribute: null
                sourceComponent: {
                    nodeName = root.model.name;
                    attribute = model.modelData;
                    connectedAttribute = attribute.isConnected ? attribute.connections[0] : null;
                    switch(attribute.type) {
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
