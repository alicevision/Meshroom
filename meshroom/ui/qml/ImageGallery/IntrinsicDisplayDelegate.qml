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
            //console.warn("keys " + Object.keys(intrinsicModel.columns[model.index]))
            //console.warn("index " + intrinsicModel.columnCount)
            console.warn("HEEELPPP " + model.display.value)
            //console.warn("Object   " + intrinsicModel.columns[model.index].display)
            switch(model.display.type)
            {
//                case "IntParam": return slider_component
//                case "FloatParam": return slider_component
                case "BoolParam": return bool_component
                default: return textField_component
            }
        }
    }

    Component {
        id: textField_component
        TextInput{
            text: model.display.value
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
        id: bool_component
        RowLayout{
            spacing: 0
            TextInput{
                text: "Bool : " + model.display.value
                padding: 12
                selectByMouse: true

                onAccepted: model.display = text

                Rectangle {
                    anchors.fill: parent
                    color: 'green'
                    z: -1
                }
            }
        }
    }




}
