.pragma library


function intToString(v) {
    // use EN locale to get comma separated thousands
    // + remove automatically added trailing decimals
    // (this 'toLocaleString' does not take any option)
    return v.toLocaleString(Qt.locale('en-US')).split('.')[0]
}

// Convert a plain text to an html escaped string.
function plainToHtml(t) {
    var escaped = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); // escape text
    return escaped.replace(/\n/g, '<br>'); // replace line breaks
}
