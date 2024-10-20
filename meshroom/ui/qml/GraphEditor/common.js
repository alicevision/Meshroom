
var statusColors = {
    "NONE": "transparent",
    "SUBMITTED": "#009688",
    "RUNNING": "#FF9800",
    "ERROR": "#F44336",
    "SUCCESS": "#4CAF50",
    "STOPPED": "#E91E63",
    "BUILD": "#66207f",
    "FIRST_RUN": "#A52A2A"
}

var statusColorsExternOverrides = {
    "SUBMITTED": "#2196F3"
}

function getChunkColor(chunk, overrides) {
    if (overrides && chunk.statusName in overrides) {
        return overrides[chunk.statusName]
    } else if(chunk.execModeName === "EXTERN"
              && chunk.statusName in statusColorsExternOverrides) {
        return statusColorsExternOverrides[chunk.statusName]
    } else if(chunk.statusName in statusColors) {
        return statusColors[chunk.statusName]
    }

    console.warn("Unknown status : " + chunk.status)
    return "magenta"
}
