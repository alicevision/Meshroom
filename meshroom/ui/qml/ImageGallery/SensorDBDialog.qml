import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Controls 1.0

MessageDialog {
    id: root

    property url sensorDatabase
    property bool readOnly: false

    signal updateIntrinsicsRequest()

    icon.text: MaterialIcons.camera
    icon.font.pointSize: 10

    modal: true
    parent: Overlay.overlay
    canCopy: false

    title: "Sensor Database"
    text: "Add missing Camera Models to the Sensor Database to improve your results."
    detailedText: "If a warning is displayed on your images, adding your Camera Model to the Sensor Database\n"+
                  "can help fix it and improve your reconstruction results."
    helperText: 'To update the Sensor Database (<a href="https://github.com/alicevision/meshroom/wiki/Add-Camera-to-database">complete guide</a>):<br>' +
                ' - Look for the "sensor width" in millimeters of your Camera Model<br>' +
                ' - Add a new line in the Database following this pattern: Make;Model;SensorWidthInMM<br>' +
                ' - Click on "' + rebuildIntrinsics.text + '" once the Database has been saved<br>' +
                ' - Contribute to the <a href="https://github.com/alicevision/AliceVision/blob/develop/src/aliceVision/sensorDB/cameraSensors.db">online Database</a>'

    ColumnLayout {
        RowLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                text: "Sensor Database:"
            }

            TextField {
                id: sensorDBTextField
                Layout.fillWidth: true
                text: Filepath.normpath(sensorDatabase)
                selectByMouse: true
                readOnly: true
            }
            MaterialToolButton {
                text: MaterialIcons.assignment
                ToolTip.text: "Copy Path"
                onClicked: {
                    sensorDBTextField.selectAll();
                    sensorDBTextField.copy();
                    ToolTip.text = "Path has been copied!"
                }
                onHoveredChanged: if(!hovered) ToolTip.text = "Copy Path"
            }
            MaterialToolButton {
                text: MaterialIcons.open_in_new
                ToolTip.text: "Open in External Editor"
                onClicked: Qt.openUrlExternally(sensorDatabase)
            }
        }
    }
    Button {
        id: rebuildIntrinsics
        text: "Update Intrinsics"
        enabled: !readOnly
        onClicked: updateIntrinsicsRequest()
        Layout.alignment: Qt.AlignCenter
    }
    standardButtons: Dialog.Close
    onAccepted: close()
}
