.pragma library

function intToString(v) {
    // Use EN locale to get comma separated thousands
    // + remove automatically added trailing decimals
    // (this 'toLocaleString' does not take any option)
    return v.toLocaleString(Qt.locale('en-US')).split('.')[0]
}

// Convert a plain text to an html escaped string.
function plainToHtml(t) {
    var escaped = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')  // Escape text
    return escaped.replace(/\n/g, '<br>')  // Replace line breaks
}

function divmod(x, y) {
    // Perform the division and get the quotient
    const quotient = Math.floor(x / y)
    // Compute the remainder
    const remainder = x % y
    return [quotient, remainder]
}

function sec2timeHMS(totalSeconds) {
    const [totalMinutes, seconds] = divmod(totalSeconds, 60.0)
    const [hours, minutes] = divmod(totalMinutes, 60.0)

    return {
        hours: hours,
        minutes: minutes,
        seconds: seconds
    }
}

function sec2timecode(timeSeconds) {
    var pad = function(num, size) { return ('000' + num).slice(size * -1) }
    var timeObj = sec2timeHMS(Math.round(timeSeconds))
    var timeStr = pad(timeObj.hours, 2) + ':' + pad(timeObj.minutes, 2) + ':' + pad(timeObj.seconds, 2)
    return timeStr
}

function sec2timeStr(timeSeconds) {
    // Need to decide the rounding precision first to propagate the right values
    if (timeSeconds >= 60.0) {
        timeSeconds = Math.round(timeSeconds)
    } else {
        timeSeconds = parseFloat(timeSeconds.toFixed(2))
    }
    var timeObj = sec2timeHMS(timeSeconds)
    var timeStr = ""
    if (timeObj.hours > 0) {
        timeStr += timeObj.hours + "h"
    }
    if (timeObj.hours > 0 || timeObj.minutes > 0) {
        timeStr += timeObj.minutes + "m"
    }
    if (timeObj.hours === 0) {
        // Seconds only matter if the elapsed time is less than 1 hour
        if (timeObj.minutes === 0) {
            // If less than a minute, keep millisecond precision
            timeStr += timeObj.seconds.toFixed(2) + "s"
        } else {
            // If more than a minute, do not need more precision than seconds
            timeStr += Math.round(timeObj.seconds) + "s"
        }
    }
    return timeStr
}

function GB2GBMBKB(GB) {
    // Convert GB to GB, MB, KB
    var GBInt = Math.floor(GB)
    var MB = Math.floor((GB - GBInt) * 1024)
    var KB = Math.floor(((GB - GBInt) * 1024 - MB) * 1024)
    return {
        GB: GBInt,
        MB: MB,
        KB: KB
    }
}

function GB2SizeStr(GB) {
    // Convert GB to a human readable size string
    // e.g. 1.23GB, 456MB, 789KB
    // We only use one unit at a time
    var sizeObj = GB2GBMBKB(GB)
    var sizeStr = ""
    if (sizeObj.GB > 0) {
        sizeStr += sizeObj.GB
        if (sizeObj.MB > 0 && sizeObj.GB < 10) {
            sizeStr += "." + Math.floor(sizeObj.MB / 1024 * 1000)
        }
        sizeStr += "GB"
    } else if (sizeObj.MB > 0) {
        sizeStr = sizeObj.MB
        if (sizeObj.KB > 0 && sizeObj.MB < 10) {
            sizeStr += "." + Math.floor(sizeObj.KB / 1024 * 1000)
        }
        sizeStr += "MB"
    } else if (sizeObj.GB === 0 && sizeObj.MB === 0) {
        sizeStr += sizeObj.KB + "KB"
    }
    return sizeStr
}
