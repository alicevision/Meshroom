.pragma library

/**
 * Perform 'GET' request on url, and bind 'callback' to onreadystatechange (with XHR objet as parameter).
 *
 * TODO: Porting to Qt6
 * TODO: This function needs to be rewritten in Python.
 * Using GET on a local file with XMLHttpRequest is disabled by default in Qt6.
 * For now, environmental variable QML_XHR_ALLOW_FILE_READ must be set to 1 to enable this feature.
 */
function get(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() { callback(xhr) }
    xhr.open("GET", url)
    xhr.send()
}
