import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MaterialIcons 2.2

RowLayout {
    id: root

    property color  defaultColor: "white"
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
        // TODO : Open messages UI
        // onClicked: statusBar.showMessage("NotImplementedError : Cannot open interface", "error", 2000)
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

        function showMessage(msg, status=undefined, duration=undefined) {
            var textColor = defaultColor
            var logLevel = "info"
            switch (status) {
                case "ok": {
                    logLevel = "info"
                    textColor = Qt.lighter("green", 1.6)
                    statusBarButton.text = MaterialIcons.check_circle
                    break
                }
                case "warning": {
                    logLevel = "warn"
                    textColor = Qt.lighter("yellow", 1.4)
                    statusBarButton.text = MaterialIcons.warning
                    break
                }
                case "error": {
                    logLevel = "error"
                    textColor = Qt.lighter("red", 1.4)
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
            statusBarField.color = textColor
            statusBarButton.contentItem.color = textColor
            statusBar.message = msg
            statusBarTimer.interval = duration !== undefined ? duration : root.interval
            statusBarTimer.restart()
        }
    }

    function showMessage(msg, status=undefined, duration=undefined) {
        statusBar.showMessage(msg, status, duration)
        MeshroomApp.forceUIUpdate()
    }
}
