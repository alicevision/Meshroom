import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

ApplicationWindow {
    id: root
    title: "Messages"
    width: 500
    height: 400
    minimumWidth: 350
    minimumHeight: 250

    SystemPalette { id: systemPalette }

    function getColor(status) {
        switch (status) {
            case "ok": return Colors.green
            case "warning": return Colors.orange
            case "error": return Colors.red
            default: return systemPalette.text
        }
    }

    function getBackgroundColor(status) {
        var color = getColor(status)
        var alphaValue = status == "info" ? 0.05 : 0.1
        return Qt.rgba(color.r, color.g, color.b, alphaValue)
    }

    function getBorderColor(status) {
        var color = getColor(status)
        var alphaValue = status == "info" ? 0.2 : 0.3
        return Qt.rgba(color.r, color.g, color.b, alphaValue)
    }

    function getStatusIcon(status) {
        switch (status) {
            case "ok": return MaterialIcons.check_circle
            case "warning": return MaterialIcons.warning
            case "error": return MaterialIcons.error
            default: return MaterialIcons.info
        }
    }

    header: ToolBar {

        background: Rectangle {
            implicitWidth: root.width
            implicitHeight: 50
            color: Qt.darker(systemPalette.base, 1.2)
        }
        
        RowLayout {
            anchors.fill: parent
            
            Text {
                Layout.fillWidth: true
                text: "Messages (" + messageListView.count + ")"
                font.bold: true
                color: Qt.darker(systemPalette.text, 1.2)
            }
            
            MaterialToolButton {
                ToolTip.text: "Clear the message list"
                text: MaterialIcons.clear_all
                font.pointSize: 16
                palette.base: systemPalette.base
                // Text color
                Component.onCompleted: {
                    contentItem.color = Qt.darker(systemPalette.text, 1.2)
                }
                onClicked: _messageController.clearMessages()
            }

            MaterialToolButton {
                ToolTip.text: "Copy the messages"
                text: MaterialIcons.content_copy
                font.pointSize: 16
                palette.base: systemPalette.base
                // Text color
                Component.onCompleted: {
                    contentItem.color = Qt.darker(systemPalette.text, 1.2)
                }
                onClicked: {
                    var msgDict = _messageController.getMessagesAsString()
                    if (msgDict !== '') {
                        Clipboard.clear()
                        Clipboard.setText(msgDict)
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: systemPalette.base

        ScrollView {
            anchors.fill: parent
            anchors.margins: 10

            ListView {
                id: messageListView
                model: _messageController.messages
                verticalLayoutDirection: ListView.TopToBottom
                spacing: 5

                delegate: Rectangle {
                    width: messageListView.width
                    height: messageLayout.implicitHeight + 16
                    color: root.getBackgroundColor(modelData.status)
                    border.color: root.getBorderColor(modelData.status)
                    border.width: 1
                    radius: 4

                    RowLayout {
                        id: messageLayout
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 12

                        // Icon
                        Text {
                            text: root.getStatusIcon(modelData.status)
                            font.pointSize: 14
                            color: root.getColor(modelData.status)
                            Layout.alignment: Qt.AlignVCenter
                        }

                        // Text
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: modelData.date
                                font.pointSize: 8
                                color: Qt.darker(systemPalette.windowText, 1.5)
                                Layout.alignment: Qt.AlignLeft
                            }

                            Text {
                                text: modelData.text
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                color: systemPalette.windowText
                                font.pointSize: 10
                            }
                        }
                    }
                }

                // Empty state
                Text {
                    anchors.centerIn: parent
                    text: "No message to display"
                    color: Qt.darker(systemPalette.windowText, 1.5)
                    font.pointSize: 12
                    visible: messageListView.count === 0
                }
            }
        }
    }
}