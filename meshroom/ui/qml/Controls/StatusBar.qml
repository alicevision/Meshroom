import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MaterialIcons 2.2

import Utils 1.0

RowLayout {
    id: root

    property color  defaultColor: Qt.darker(palette.text, 1.2)
    property string defaultIcon : MaterialIcons.circle
    property int    interval    : 5000
    property bool   logMessage  : false

    TextField {
        id: statusBarField
        Layout.fillHeight: true
        readOnly: true
        selectByMouse: true
        text: statusBar.message
        color: defaultColor
        background: Item {}
        visible: statusBar.message !== ""
    }

    // TODO : Idea for later : implement a ProgressBar here

    MaterialToolButton {
        id: statusBarButton
        Layout.fillHeight: true
        Layout.preferredWidth: 17
        visible: true
        font.pointSize: 8
        text: defaultIcon
        ToolTip.text: "Open Messages UI"
        onClicked: {
            var component = Qt.createComponent("StatusMessages.qml")
            var window    = component.createObject(root)
            window.show()
        }
        Component.onCompleted: {
            statusBarButton.contentItem.color = defaultColor
        }
    }

    Timer {
        id: statusBarTimer
        interval: root.interval
        running: false
        repeat: false
        onTriggered: {
            // Erase message and reset button icon
            statusBar.message = ""
            statusBarField.color = defaultColor
            statusBarButton.contentItem.color = defaultColor
            statusBarButton.text = defaultIcon
        }
    }

    QtObject {
        id: statusBar
        property string message: ""

        function showMessage(msg, status=undefined, duration=root.interval) {
            var textColor = defaultColor
            var logLevel = "info"
            switch (status) {
                case "ok": {
                    statusBarField.color = Colors.green
                    statusBarButton.text = MaterialIcons.check_circle
                    break
                }
                case "warning": {
                    logLevel = "warn"
                    statusBarField.color = Colors.orange
                    statusBarButton.text = MaterialIcons.warning
                    break
                }
                case "error": {
                    logLevel = "error"
                    statusBarField.color = Colors.red
                    statusBarButton.text = MaterialIcons.error
                    break
                }
                default: {
                    statusBarButton.text = defaultIcon
                }
            }
            if (logMessage === true) {
                console.log("[Message][" + logLevel.toUpperCase().padEnd(5) + "] " + msg)
            }
            statusBarButton.contentItem.color = statusBarField.color
            statusBar.message = msg
            statusBarTimer.interval = duration
            statusBarTimer.restart()
            MeshroomApp.forceUIUpdate()
        }
    }

    function showMessage(msg, status=undefined, duration=root.interval) {
        statusBar.showMessage(msg, status, duration)
        // Add message to the message list
        _messageController.storeMessage(msg, status)
    }

    Connections {
        target: _messageController
        function onMessage(message, color, duration) {
            root.showMessage(message, color, duration)
        }
    }
}
