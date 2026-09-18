import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import Utils 1.0
import MaterialIcons 2.2

Item {
    id: root

    property var nodeAttributeEditor
    property var palette: null

    readonly property color colorAccent: "#5294e2"
    readonly property color colorTextMuted: "#9a9a9a"

    implicitWidth: 520
    implicitHeight: column.implicitHeight + 24

    Rectangle {
        anchors.fill: parent
        color: palette.window
        radius: 6
    }

    Connections {
        target: root.nodeAttributeEditor
        function onErrorOccurred(message) {
            errorLabel.text = message
            errorLabel.visible = true
            errorTimer.restart()
        }
    }

    // Get the component corresponding to an attribute.
    function valueDisplayComponent(attrType) {
        switch (attrType) {
            case "IntParam":
                return intValueComponent
            case "FloatParam":
                return floatValueComponent
            case "BoolParam":
                return boolValueComponent
            case "StringParam":
            case "File":
            default:
                return stringValueComponent
        }
    }

    // Reads the current value out of a loaded value widget, regardless of type.
    function readValue(loaderItem) {
        if (loaderItem.hasOwnProperty("checked"))
            return loaderItem.checked ? "true" : "false"
        if (loaderItem.hasOwnProperty("value") && !loaderItem.hasOwnProperty("text"))
            return String(loaderItem.value)
        return loaderItem.text
    }

    Component {
        id: stringValueComponent
        TextField {
            placeholderText: "value"
            selectByMouse: true
            background: Rectangle {
                radius: 8
                color: root.palette.base
                border.color: Qt.darker(root.palette.base, 1.4)
            }
        }
    }

    Component {
        id: intValueComponent
        SpinBox {
            from: -32768
            to: 32767
            editable: true
            background: Rectangle {
                radius: 8
                color: root.palette.base
                border.color: Qt.darker(root.palette.base, 1.4)
            }
        }
    }

    Component {
        id: floatValueComponent
        TextField {
            placeholderText: "0.0"
            validator: DoubleValidator {}
            selectByMouse: true
            background: Rectangle {
                radius: 8
                color: root.palette.base
                border.color: Qt.darker(root.palette.base, 1.4)
            }
        }
    }

    Component {
        id: boolValueComponent
        CheckBox {
            indicator: Rectangle {
                implicitWidth: 16
                implicitHeight: 16
                y: parent.height / 2 - height / 2
                radius: 3
                border.color: root.palette.mid

                Rectangle {
                    width: 12
                    height: 12
                    x: 2
                    y: 2
                    radius: 2
                    color: parent.parent.down ? root.palette.mid : root.palette.accent
                    visible: parent.parent.checked
                }
            }
        }
    }

    ColumnLayout {
        id: column
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: "Inputs"
                font.pixelSize: 16
                font.bold: true
            }

            Item { Layout.fillWidth: true }

            Label {
                text: listView.count + (listView.count === 1 ? " input" : " inputs")
                color: root.colorTextMuted
                font.pixelSize: 12
            }
        }

        // Error label + timer that resets after 3 seconds

        Label {
            id: errorLabel
            color: Colors.firebrick
            visible: false
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            font.pixelSize: 12
        }

        Timer {
            id: errorTimer
            interval: 3000
            running: false
            repeat: false
            onTriggered: errorLabel.visible = false
        }

        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight, 280)
            clip: true
            model: root.nodeAttributeEditor ? root.nodeAttributeEditor.inputsModel : null
            spacing: 6

            Label {
                anchors.centerIn: parent
                visible: listView.count === 0
                text: "No inputs yet"
                color: root.colorTextMuted
                font.italic: true
            }

            delegate: Rectangle {
                width: listView.width
                height: rowLayout.implicitHeight + 16
                radius: 5
                color: Qt.lighter(root.palette.base, rowMouseArea.containsMouse ? 1.4 : 1.2)
                border.color: root.palette.mid
                border.width: 1

                Behavior on color { ColorAnimation { duration: 100 } }

                MouseArea {
                    id: rowMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                }

                RowLayout {
                    id: rowLayout
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 8
                    spacing: 15

                    Rectangle {
                        Layout.preferredWidth: 6
                        Layout.preferredHeight: 6
                        radius: 3
                        color: root.palette.accent
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Label {
                        id: attrLabel
                        text: `<b>${model.label}</b>   <font color="${root.palette.lightgrey}"><i>(${model.name})</i></font>`
                        Layout.preferredWidth: 170
                        elide: Text.ElideRight

                        MouseArea {
                            id: _mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton // hover only, don't swallow clicks
                        }

                        ToolTip {
                            delay: 200
                            text: `<b>${model.type}</b>` + (model.description ? `<b>:</b> ${model.description}` : "")
                            visible: _mouseArea.containsMouse
                            x: -width - 40
                            y: (attrLabel.height - height) / 2
                        }
                    }

                    Loader {
                        Layout.fillWidth: true
                        sourceComponent: valueDisplayComponent(model.type)
                        onLoaded: {
                            if (item.hasOwnProperty("sourceAttribute"))
                                item.sourceAttribute = model.attributeObject
                            if (item.hasOwnProperty("checked"))
                                item.checked = (model.value === true || value === "true")
                            else if (item.hasOwnProperty("value") && !item.hasOwnProperty("text"))
                                item.value = Number(model.value)
                            else
                                item.text = value
                            item.enabled = false
                        }
                    }

                    MaterialToolButton {
                        text: MaterialIcons.close
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        font.pixelSize: 12
                        background: Rectangle {
                            radius: 4
                            color: parent.hovered ? Colors.firebrick : "transparent"
                        }
                        onClicked: {
                            if (root.nodeAttributeEditor)
                                root.nodeAttributeEditor.removeInput(model.name)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: root.palette.mid
        }

        // --- New input layout ---

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "New input"
                font.pixelSize: 14
                font.bold: true
            }

            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 10
                rowSpacing: 8

                Label {
                    text: "Type"
                    color: root.colorTextMuted
                    Layout.preferredWidth: 90
                }
                ComboBox {
                    id: newType
                    Layout.fillWidth: true
                    model: root.nodeAttributeEditor ? root.nodeAttributeEditor.attrTypes : []
                }

                Label {
                    text: "Name"
                    color: root.colorTextMuted
                    Layout.preferredWidth: 90
                }
                TextField {
                    id: newName
                    Layout.fillWidth: true
                    placeholderText: "attribute name"
                    selectByMouse: true
                    background: Rectangle {
                        radius: 8
                        color: root.palette.base
                        border.color: Qt.darker(root.palette.base, 1.4)
                    }
                }

                Label {
                    text: "Label"
                    color: root.colorTextMuted
                    Layout.preferredWidth: 90
                }
                TextField {
                    id: newLabel
                    Layout.fillWidth: true
                    placeholderText: "display label"
                    selectByMouse: true
                    background: Rectangle {
                        radius: 8
                        color: root.palette.base
                        border.color: Qt.darker(root.palette.base, 1.4)
                    }
                }

                Label {
                    text: "Description"
                    color: root.colorTextMuted
                    Layout.preferredWidth: 90
                }
                TextField {
                    id: newDescription
                    Layout.fillWidth: true
                    placeholderText: "description"
                    selectByMouse: true
                    background: Rectangle {
                        radius: 8
                        color: root.palette.base
                        border.color: Qt.darker(root.palette.base, 1.4)
                    }
                }

                Label {
                    text: "Value"
                    color: root.colorTextMuted
                    Layout.preferredWidth: 90
                }
                Loader {
                    id: newValueLoader
                    Layout.fillWidth: true
                    sourceComponent: valueDisplayComponent(newType.currentText)
                    onLoaded: {
                        if (item.hasOwnProperty("sourceAttribute"))
                            item.sourceAttribute = model.attributeObject
                    }
                }
            }
        }

        // Add button

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4

            Item { Layout.fillWidth: true }

            Button {
                text: MaterialIcons.format_list_bulleted_add + " Add input"
                padding: 10
                highlighted: true
                
                background: Rectangle {
                    color: parent.pressed ? Colors.green : (parent.hovered ? root.palette.accent : root.palette.mid)
                    radius: height / 2
                }
                onClicked: {
                    if (!root.nodeAttributeEditor)
                        return
                    var value = newValueLoader.item ? readValue(newValueLoader.item) : ""
                    root.nodeAttributeEditor.addInput(
                        newType.currentText,
                        newName.text,
                        newLabel.text,
                        newDescription.text,
                        value
                    )
                    newName.clear()
                    newLabel.clear()
                    newDescription.clear()
                    newValueLoader.active = false
                    newValueLoader.active = true
                    listView.forceLayout()
                }
            }
        }
    }
}
