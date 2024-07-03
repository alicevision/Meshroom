import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11
import Controls 1.0
import Utils 1.0
import MaterialIcons 2.2

import Qt.labs.platform 1.0 as Platform
import QtQuick.Dialogs 1.3

Item {
    id: root

    function formatInput(text) {
        var lines = text.split("\n")
        for (let i = 0; i < lines.length; ++i) {
            lines[i] = ">>> " + lines[i]
        }
        return lines.join("\n")
    }

    function processScript() {
        output.clear()
        var ret = ScriptEditorManager.process(input.text)
        output.text = formatInput(input.text) + "\n\n" + ret
        input.clear()
    }

    function loadScript(fileUrl) {
        var request = new XMLHttpRequest()
        request.open("GET", fileUrl, false)
        request.send(null)
        return request.responseText
    }

    function saveScript(fileUrl, content) {
        var request = new XMLHttpRequest()
        request.open("PUT", fileUrl, false)
        request.send(content)
        return request.status
    }

    implicitWidth: 500
    implicitHeight: 500

    Platform.FileDialog {
        id: loadScriptDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Load Script"
        nameFilters: ["Python Script (*.py)"]
        onAccepted: {
            input.clear()
            input.text = loadScript(currentFile)
        }
    }

    Platform.FileDialog {
        id: saveScriptDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Save script"
        nameFilters: ["Python Script (*.py)"]
        fileMode: Platform.FileDialog.SaveFile

        signal closed(var result)

        onAccepted: {
            if (Filepath.extension(currentFile) != ".py")
                currentFile = currentFile + ".py"
            var ret = saveScript(currentFile, input.text)
            if (ret)
                closed(Platform.Dialog.Accepted)
            else
                closed(Platform.Dialog.Rejected)
        }

        onRejected: closed(Platform.Dialog.Rejected)
    }

    ColumnLayout {
        anchors.fill: parent

        RowLayout {
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter

            Item {
                Layout.fillWidth: true
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.download
                ToolTip.text: "Load Script"

                onClicked: {
                    loadScriptDialog.open()
                }
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.upload
                ToolTip.text: "Save Script"

                onClicked: {
                    saveScriptDialog.open()
                }
            }

            Item {
                width: executeButton.width
            }

            MaterialToolButton {
                id: executeButton
                font.pointSize: 13
                text: MaterialIcons.slideshow
                ToolTip.text: "Execute Script"

                onClicked: {
                    processScript()
                }
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.cancel_presentation
                ToolTip.text: "Clear Output Window"

                onClicked: {
                    output.clear()
                }
            }

            Item {
                width: executeButton.width
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.history
                ToolTip.text: "Get Previous Script"

                onClicked: {
                    var ret = ScriptEditorManager.getPreviousScript()

                    if (ret != "") {
                        input.clear()
                        input.text = ret
                    }
                }
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.update
                ToolTip.text: "Get Next Script"

                onClicked: {
                    var ret = ScriptEditorManager.getNextScript()

                    if (ret != "") {
                        input.clear()
                        input.text = ret
                    }
                }
            }

            MaterialToolButton {
                font.pointSize: 13
                text: MaterialIcons.backspace
                ToolTip.text: "Clear History"

                onClicked: {
                    ScriptEditorManager.clearHistory()
                    input.clear()
                    output.clear()
                }
            }

            Item {
                Layout.fillWidth: true
            }
        }

        RowLayout {
            Label {
                text: "Input"
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Label {
                text: "Output"
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            width: root.width

            Rectangle {
                id: inputArea
                Layout.fillHeight: true
                Layout.fillWidth: true

                color: palette.base

                ListView {
                    id: lineNumbers
                    property TextMetrics textMetrics: TextMetrics { text: "9999" }
                    model: input.text.split(/\n/g)
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: lineNumbers.textMetrics.boundingRect.width
                    clip: false

                    delegate: Rectangle {
                        width: lineNumbers.width
                        height: lineText.height
                        color: palette.mid
                        Text {
                            id: lineNumber
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: index + 1
                            font.bold: true
                            color: palette.text
                        }

                        Text {
                            id: lineText
                            width: flickableInput.width
                            text: modelData
                            visible: false
                            wrapMode: Text.WordWrap
                        }
                    }

                    onContentYChanged: {
                        if (!moving)
                            return
                        flickableInput.contentY = contentY
                    }
                }

                Flickable {
                    id: flickableInput
                    width: parent.width
                    height: parent.height
                    contentWidth: width
                    contentHeight: height

                    anchors.left: lineNumbers.right
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    TextArea.flickable: TextArea {
                        id: input

                        text: {
                            var str = "from meshroom.ui import uiInstance\n\n"
                            str += "graph = uiInstance.activeProject.graph\n"
                            str += "for node in graph.nodes:\n"
                            str += "    print(node.name)"
                            return str
                        }
                        font: lineNumbers.textMetrics.font
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                        wrapMode: Text.WordWrap
                        selectByMouse: true
                        padding: 0

                        onPressed: {
                            root.forceActiveFocus()
                        }

                        Keys.onPressed: {
                            if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return) && event.modifiers === Qt.ControlModifier) {
                                processScript()
                            }
                        }
                    }

                    onContentYChanged: {
                        if (lineNumbers.moving)
                            return
                        lineNumbers.contentY = contentY
                    }
                }
            }
            
            Rectangle {
                id: outputArea
                Layout.fillHeight: true
                Layout.fillWidth: true

                color: palette.base

                Flickable {
                    width: parent.width
                    height: parent.height
                    contentWidth: width
                    contentHeight: height

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    TextArea.flickable: TextArea {
                        id: output

                        readOnly: true
                        selectByMouse: true
                        padding: 0
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}