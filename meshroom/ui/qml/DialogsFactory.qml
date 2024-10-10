import QtQuick
import Controls 1.0

/**
 * DialogsFactory is utility object to instantiate generic purpose Dialogs.
 */

QtObject {

    readonly property string defaultErrorText: "An unexpected error has occurred"

    property Component infoDialog: Component {
        MessageDialog {
            title: "Info"
            preset: "Info"
            visible: true
        }
    }
    property Component warningDialog: Component {
        MessageDialog {
            title: "Warning"
            preset: "Warning"
            visible: true
        }
    }
    property Component errorDialog: Component {
        id: errorDialog
        MessageDialog {
            title: "Error"
            preset: "Error"
            text: defaultErrorText
            visible: true
        }
    }

    function info(window) {
        return infoDialog.createObject(window)
    }

    function warning(window) {
        return warningDialog.createObject(window)
    }

    function error(window) {
        return errorDialog.createObject(window)
    }
}
