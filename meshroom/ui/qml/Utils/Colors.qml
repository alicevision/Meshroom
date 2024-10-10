pragma Singleton
import QtQuick
import QtQuick.Controls

/**
 * Singleton that gathers useful colors, shades and system palettes.
 */

QtObject {
    property SystemPalette sysPalette: SystemPalette {}
    property SystemPalette disabledSysPalette: SystemPalette { colorGroup: SystemPalette.Disabled }

    readonly property color green: "#4CAF50"
    readonly property color orange: "#FF9800"
    readonly property color yellow: "#FFEB3B"
    readonly property color red: "#F44336"
    readonly property color blue: "#03A9F4"
    readonly property color cyan: "#00BCD4"
    readonly property color pink: "#E91E63"
    readonly property color lime: "#CDDC39"
    readonly property color grey: "#555555"
    readonly property color lightgrey: "#999999"

    readonly property var statusColors: {
        "NONE": "transparent",
        "SUBMITTED": cyan,
        "RUNNING": orange,
        "ERROR": red,
        "SUCCESS": green,
        "STOPPED": pink
    }

    readonly property var ghostColors: {
        "SUBMITTED": Qt.darker(cyan, 1.5),
        "RUNNING": Qt.darker(orange, 1.5),
        "STOPPED": Qt.darker(pink, 1.5)
    }

    readonly property var statusColorsExternOverrides: {
        "SUBMITTED": "#2196F3"
    }

    readonly property var durationColorScale: [
        {"time": 0, "color": grey},
        {"time": 5, "color": green},
        {"time": 20, "color": yellow},
        {"time": 90, "color": red}
    ]

    function getChunkColor(chunk, overrides) {
        if (overrides && chunk.statusName in overrides) {
            return overrides[chunk.statusName]
        } else if (chunk.execModeName === "EXTERN" && chunk.statusName in statusColorsExternOverrides) {
            return statusColorsExternOverrides[chunk.statusName]
        } else if (chunk.nodeName !== chunk.statusNodeName && chunk.statusName in ghostColors) {
            return ghostColors[chunk.statusName]
        } else if (chunk.statusName in statusColors) {
            return statusColors[chunk.statusName]
        }
        console.warn("Unknown status : " + chunk.status)
        return "magenta"
    }

    function toRgb(color) {
        return [
            parseInt(color.toString().substr(1, 2), 16) / 255, 
            parseInt(color.toString().substr(3, 2), 16) / 255, 
            parseInt(color.toString().substr(5, 2), 16) / 255
        ]
    }

    function interpolate(c1, c2, u) {
        let rgb1 = toRgb(c1)
        let rgb2 = toRgb(c2)
        return Qt.rgba(
            rgb1[0] * (1 - u) + rgb2[0] * u,
            rgb1[1] * (1 - u) + rgb2[1] * u,
            rgb1[2] * (1 - u) + rgb2[2] * u
        )
    }

    function durationColor(t) {
        if (t < durationColorScale[0].time) {
            return durationColorScale[0].color
        }
        if (t > durationColorScale[durationColorScale.length-1].time) {
            return durationColorScale[durationColorScale.length-1].color
        }
        for (let idx = 1; idx < durationColorScale.length; idx++) {
            if (t < durationColorScale[idx].time) {
                let u = (t - durationColorScale[idx - 1].time) / (durationColorScale[idx].time - durationColorScale[idx - 1].time)
                return interpolate(durationColorScale[idx - 1].color, durationColorScale[idx].color, u)
            }
        }
    }
}
