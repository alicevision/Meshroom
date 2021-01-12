pragma Singleton
import QtQuick 2.9
import QtQuick.Controls 2.4

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

    function getChunkColor(chunk, overrides)
    {
        if(overrides && chunk.statusName in overrides)
        {
            return overrides[chunk.statusName]
        }
        else if(chunk.execModeName === "EXTERN"
           && chunk.statusName in statusColorsExternOverrides)
        {
            return statusColorsExternOverrides[chunk.statusName]
        }
        else if(chunk.nodeName !== chunk.statusNodeName && chunk.statusName in ghostColors) {
            return ghostColors[chunk.statusName]
        }
        else if(chunk.statusName in statusColors)
        {
            return statusColors[chunk.statusName]
        }
        console.warn("Unknown status : " + chunk.status)
        return "magenta"
    }
}
