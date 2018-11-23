.pragma library


function intToString(v) {
    // use EN locale to get comma separated thousands
    // + remove automatically added trailing decimals
    // (this 'toLocaleString' does not take any option)
    return v.toLocaleString(Qt.locale('en-US')).split('.')[0]
}
