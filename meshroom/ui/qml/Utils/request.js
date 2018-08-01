.pragma library

/**
 * Perform 'GET' request on url, and bind 'callback' to onreadystatechange (with XHR objet as parameter).
 */
function get(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() { callback(xhr) }
    xhr.open("GET", url)
    xhr.send()
}
