import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Label {

    id: control

    text: qsTr("Label")
    color: enabled ? Globals.text.color.normal : Globals.text.color.disabled
    elide: Text.ElideRight
    wrapMode: Text.WrapAnywhere
    maximumLineCount: 1
    verticalAlignment: Text.AlignVCenter
    font.pixelSize: Globals.text.size.normal

    states: [
        State {
            name: "xsmall"
            PropertyChanges {
                target: control
                font.pixelSize: Globals.text.size.xsmall
            }
        },
        State {
            name: "small"
            PropertyChanges {
                target: control
                font.pixelSize: Globals.text.size.small
            }
        },
        State {
            name: "large"
            PropertyChanges {
                target: control
                font.pixelSize: Globals.text.size.large
            }
        },
        State {
            name: "xlarge"
            PropertyChanges {
                target: control
                font.pixelSize: Globals.text.size.xlarge
            }
        }
    ]

}
