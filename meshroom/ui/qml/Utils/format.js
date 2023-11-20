.pragma library


function intToString(v) {
    // use EN locale to get comma separated thousands
    // + remove automatically added trailing decimals
    // (this 'toLocaleString' does not take any option)
    return v.toLocaleString(Qt.locale('en-US')).split('.')[0]
}

// Convert a plain text to an html escaped string.
function plainToHtml(t) {
    var escaped = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') // escape text
    return escaped.replace(/\n/g, '<br>') // replace line breaks
}

function divmod(x, y) {
    // Perform the division and get the quotient
    const quotient = Math.floor(x / y);
    // Compute the remainder
    const remainder = x % y;
    return [quotient, remainder];
}

function sec2timeHMS(totalSeconds) {
    const [totalMinutes, seconds] = divmod(totalSeconds, 60.0)
    const [hours, minutes] = divmod(totalMinutes, 60.0)

    return {
        hours: hours,
        minutes: minutes,
        seconds: seconds
    };
}

function sec2timecode(timeSeconds) {
    var pad = function(num, size) { return ('000' + num).slice(size * -1) }
    var timeObj = sec2timeHMS(Math.round(timeSeconds))
    var timeStr = pad(timeObj.hours, 2) + ':' + pad(timeObj.minutes, 2) + ':' + pad(timeObj.seconds, 2)
    return timeStr
}

function sec2timeStr(timeSeconds) {
    // Need to decide the rounding precision first
    // to propagate the right values
    if(timeSeconds >= 60.0) {
        timeSeconds = Math.round(timeSeconds)
    } else {
        timeSeconds = parseFloat(timeSeconds.toFixed(2))
    }
    var timeObj = sec2timeHMS(timeSeconds)
    var timeStr = ""
    if(timeObj.hours > 0) {
        timeStr += timeObj.hours + "h"
    }
    if(timeObj.hours > 0 || timeObj.minutes > 0) {
        timeStr += timeObj.minutes + "m"
    }
    if(timeObj.hours === 0) {
        // seconds only matter if the elapsed time is less than 1 hour
        if(timeObj.minutes === 0) {
            // If less than a minute, keep millisecond precision
            timeStr += timeObj.seconds.toFixed(2) + "s"
        } else {
            // If more than a minute, do not need more precision than seconds
            timeStr += Math.round(timeObj.seconds) + "s"
        }
    }
    return timeStr
}
