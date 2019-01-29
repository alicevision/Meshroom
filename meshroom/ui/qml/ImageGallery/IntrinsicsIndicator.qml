import QtQuick 2.9
import QtQuick.Controls 2.4
import MaterialIcons 2.2
import Utils 1.0


/**
 * Display camera initialization status and the value of metadata
 * that take part in this process.
 */
ImageBadge {
    id: root

    property string intrinsicInitMode
    property var metadata: ({})

    // access useful metadata
    readonly property var make: metadata["Make"]
    readonly property var model: metadata["Model"]
    readonly property var focalLength: metadata["Exif:FocalLength"]
    readonly property var focalLength35: metadata["Exif:FocalLengthIn35mmFilm"]
    readonly property var bodySerialNumber: metadata["Exif:BodySerialNumber"]
    readonly property var lensSerialNumber: metadata["Exif:LensSerialNumber"]
    readonly property var sensorWidth: metadata["AliceVision:SensorWidth"]
    readonly property var sensorWidthEstimation: metadata["AliceVision:SensorWidthEstimation"]

    property string statusText: ""
    property string detailsText: ""
    property string helperText: ""

    text: MaterialIcons.camera

    function metaStr(value) {
        return value || "<i>undefined</i>"
    }

    ToolTip.text: "<b>Camera Intrinsics: " + statusText + "</b><br>"
                  + (detailsText ? detailsText + "<br>" : "")
                  + (helperText ? helperText + "<br>" : "")
                  + "<br>"
                  + "[Metadata]<br>"
                  + " - Make: " + metaStr(make) + "<br>"
                  + " - Model: " + metaStr(model) + "<br>"
                  + " - FocalLength: " + metaStr(focalLength) + "<br>"
                  + ((focalLength && sensorWidth) ? "" : " - FocalLengthIn35mmFilm: " + metaStr(focalLength35) + "<br>")
                  + " - SensorWidth: " + metaStr(sensorWidth) + (sensorWidthEstimation ? " (estimation: "+ sensorWidthEstimation + ")" : "")
                  + ((bodySerialNumber || lensSerialNumber) ? "" : "<br><br>Warning: SerialNumber metadata is missing.<br> Images from different devices might incorrectly share the same camera internal settings.")


    state: intrinsicInitMode ? intrinsicInitMode : "unknown"

    states: [
        State {
            name: "calibrated"
            PropertyChanges {
                target: root
                color: Colors.green
                statusText: "Calibrated"
                detailsText: "Focal Length has been initialized externally."
            }
        },
        State {
            name: "estimated"
            PropertyChanges {
                target: root
                statusText: sensorWidth ? "Estimated" : "Approximated"
                color: sensorWidth ? Colors.green : Colors.yellow
                detailsText: "Focal Length was estimated from Metadata" + (sensorWidth ? " and Sensor Database." : " only.")
                helperText: !sensorWidth ? "Add your Camera Model to the Sensor Database for more accurate results." : ""
            }
        },
        State {
            name: "unknown"
            PropertyChanges {
                target: root
                color: focalLength ? Colors.orange : Colors.red
                statusText: "Unknown"
                detailsText: "Focal Length could not be determined from metadata. <br>"
                            + "The default Field of View value was used as a fallback, which may lead to inaccurate result or failure."
                helperText: "Check for missing Image metadata"
                            + (make && model && !sensorWidth ? " and/or add your Camera Model to the Sensor Database." : ".")
            }
        },
        State {
            // fallback status when initialization mode is unset
            name: "none"
            PropertyChanges {
                target: root
                visible: false
            }
        }

    ]
}
