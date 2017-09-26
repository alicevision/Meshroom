import QtQuick 2.5
import QtQuick.Controls 1.4 // as Controls1
//import QtQuick.Controls 2.2
import QtQuick.Layouts 1.1

ApplicationWindow {
    id: _window

    width: 1280
    height: 720
    visible: true
    title: "Meshroom"
    color: "#fafafa"

    property variant node: null

    Connections {
        target: _reconstruction.undoStack
        onIndexChanged: graphStr.update()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        Row
        {
            Layout.fillWidth: true
            TextField {
                id: filepath
                width: 200
            }
            Button {
                text: "Load"
                onClicked: _reconstruction.graph.load(filepath.text)
            }

            Button {
                text: "Add Node"
                onClicked: {
                    _reconstruction.addNode("FeatureExtraction")
                }
            }

            Item {width: 4; height: 1}

            Button {
                text: "Undo"
                activeFocusOnPress: true
                enabled: _reconstruction.undoStack.canUndo
                tooltip:  'Undo "' +_reconstruction.undoStack.undoText +'"'
                onClicked: {
                    _reconstruction.undoStack.undo()
                }
            }
            Button {
                text: "Redo"
                activeFocusOnPress: true
                enabled: _reconstruction.undoStack.canRedo
                tooltip:  'Redo "' +_reconstruction.undoStack.redoText +'"'
                onClicked: {
                    _reconstruction.undoStack.redo()
                }
            }
        }

        RowLayout{
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                Layout.fillHeight: true
                Layout.preferredWidth: 150
                model: _reconstruction.graph.nodes
                onCountChanged: {
                    graphStr.update()
                }
                spacing: 2
                delegate: Rectangle {
                    width: 130
                    height: 40
                    Label {
                        text: object.name
                        anchors.centerIn: parent
                    }

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.AllButtons
                        onClicked: {
                            if(mouse.button == Qt.RightButton)
                                _reconstruction.removeNode(object)
                            else
                                _window.node = object
                        }

                    }
                    color: "#81d4fa"
                    border.color: _window.node == object ? Qt.darker(color) : "transparent"
                }
            }

            ListView {
                id: attributesListView
                Layout.fillHeight: true
                Layout.fillWidth: true
                model: _window.node != null ? _window.node.attributes : null
                delegate: RowLayout {
                    width: attributesListView.width
                    spacing: 4
                    Label {
                        text: object.label
                        anchors.verticalCenter: parent.verticalCenter
                        Layout.preferredWidth: 200
                    }
                    TextField {
                        text: object.value
                        Layout.fillWidth: true
                        onEditingFinished: _reconstruction.setAttribute(object, text)
                    }
                }
            }


            TextArea {
                id: graphStr
                Layout.preferredWidth: 400
                Layout.fillHeight: true
                wrapMode: TextEdit.WrapAnywhere
                selectByMouse: true
                readOnly: true
                function update() {
                    graphStr.text = _reconstruction.graph.asString()
                }
            }
        }
    }
}
