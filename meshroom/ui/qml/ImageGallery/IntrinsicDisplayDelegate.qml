import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

RowLayout {
    id: root

    Layout.fillWidth: true

    property variant attribute: null
    property bool readOnly: false
    Loader {
        Layout.fillWidth: true

        sourceComponent: {
            console.warn("keys " + Object.keys(model.model))
            console.warn("Object   " + model.model.objectName)
            switch(Object.keys(model)[model.index])
            {
            //case "ChoiceParam": return attribute.desc.exclusive ? comboBox_component : multiChoice_component
            case "object": return object_component
            case "FloatParam": return slider_component
            case "BoolParam": return checkbox_component
            case "ListAttribute": return listAttribute_component
            case "GroupAttribute": return groupAttribute_component
            default: return textField_component
            }
        }

    }
    Component {
        id: textField_component
        TextInput{
            text: model.display
            padding: 12
            selectByMouse: true

            onAccepted: model.display = text

            Rectangle {
                anchors.fill: parent
                color: "#efefef"
                z: -1
            }
        }
    }

    Component {
        id: focal_length_component
        RowLayout{
            TextInput{
                text: model.display.x
                padding: 12
                selectByMouse: true

                onAccepted: model.display = text

                Rectangle {
                    anchors.fill: parent
                    color: model.index%2 ? parent.palette.window : Qt.darker(parent.palette.window, 1.1)
                    z: -1
                }
            }
            TextInput{
                text: model.display.y
                padding: 12
                selectByMouse: true

                onAccepted: model.display = text

                Rectangle {
                    anchors.fill: parent
                    color: model.index%2 ? parent.palette.window : Qt.darker(parent.palette.window, 1.1)
                    z: -1
                }
            }
        }
    }




}
