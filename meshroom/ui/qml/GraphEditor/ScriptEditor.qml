import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

import Qt.labs.platform 1.0 as Platform

import ScriptEditor 1.0

Item {
    id: root

    function replace(text, string, replacement) {
        /*
         * Replaces all occurences of the string in the text
         * @param text - overall text
         * @param string - the string to be replaced in the text
         * @param replacement - the replacement of the string
         */
        // Split with the string
        let lines = text.split(string)
        // Return the overall text joined with the replacement
        return lines.join(replacement)
    }

    function formatInput(text) {
        /*
         * Formats the text to be displayed as the input script executed
         */

        // Replace the text to be RichText Supportive
        return "<font color=#868686>" + replace(text, "\n", "<br>") + "</font><br><br>"
    }

    function formatOutput(text) {
        /*
         * Formats the text to be displayed as the result of the script executed
         */

        // Replace the text to be RichText Supportive
        return "<font color=#49a1f3>" + "Result: " + replace(text, "\n", "<br>") + "</font><br><br>"
    }

    function processScript(text = "") {
        // Use either the provided/selected or the entire script
        text = text || input.text

        // Execute the process and fetch back the return for it
        var ret = ScriptEditorManager.process(text)

        // Append the input script and the output result to the output console
        output.append(formatInput(text) + formatOutput(ret))

        // Save the entire script after executing the commands
        ScriptEditorManager.saveScript(input.text)
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

            MaterialToolButton {
                font.pointSize: 18
                text: MaterialIcons.download
                ToolTip.text: "Load Script"

                onClicked: {
                    loadScriptDialog.open()
                }
            }

            MaterialToolButton {
                font.pointSize: 18
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
                font.pointSize: 18
                text: MaterialIcons.slideshow
                ToolTip.text: "Execute Script"

                onClicked: {
                    root.processScript()
                }
            }

            MaterialToolButton {
                font.pointSize: 18
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
                font.pointSize: 18
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
                font.pointSize: 18
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
                font.pointSize: 18
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

        MSplitView {
            id: topBottomSplit
            Layout.fillHeight: true
            Layout.fillWidth: true

            orientation: Qt.Vertical
        
            // Output Text Area -- Shows the output for the executed script(s)
            Rectangle {
                id: outputArea

                // Has a minimum height
                SplitView.minimumHeight: 80

                color: palette.base

                Flickable {
                    width: parent.width
                    height: parent.height
                    contentWidth: width
                    contentHeight: ( output.lineCount + 5 ) * output.font.pixelSize // + 5 lines for buffer to be scrolled and visibility

                    ScrollBar.vertical: MScrollBar {}

                    TextArea.flickable: TextArea {
                        id: output

                        readOnly: true
                        selectByMouse: true
                        padding: 0
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap

                        textFormat: Text.RichText
                    }
                }
            }

            // Input Text Area -- Holds the input scripts to be executed
            Rectangle {
                id: inputArea

                SplitView.fillHeight: true

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
                    contentHeight: ( input.lineCount + 5 ) * input.font.pixelSize // + 5 lines for buffer to be scrolled and visibility

                    anchors.left: lineNumbers.right
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom

                    ScrollBar.vertical: MScrollBar {}

                    TextArea.flickable: TextArea {
                        id: input

                        text: ScriptEditorManager.loadLastScript()

                        font: lineNumbers.textMetrics.font
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                        wrapMode: Text.WordWrap
                        selectByMouse: true
                        padding: 0

                        onPressed: {
                            root.forceActiveFocus()
                        }

                        Keys.onPressed: function(event) {
                            if ((event.key === Qt.Key_Enter || event.key === Qt.Key_Return) && event.modifiers === Qt.ControlModifier) {
                                root.processScript(input.selectedText)
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

            // Syntax Highlights for the Input Area for Python Based Syntax
            PySyntaxHighlighter {
                id: syntaxHighlighter
                // The document to highlight
                textDocument: input.textDocument
            }
        }
    }
}