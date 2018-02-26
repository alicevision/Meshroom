/* Utility functions to manipulate file paths */

/// Returns the directory name of the given path.
function dirname(path) {
    return path.substring(0, path.lastIndexOf('/'))
}

/// Returns the basename (file.extension) of the given path.
function basename(path) {
    return path.substring(path.lastIndexOf('/') + 1, path.length)
}

/// Return the extension (prefixed by a '.') of the given path.
function extension(path) {
    var dot_pos = path.lastIndexOf('.');
    return dot_pos > -1 ? path.substring(dot_pos, path.length) : ""
}

/// Return whether the given path is a path to a file.
/// (only based on the fact that the last portion of the path
/// matches the 'basename.extension' pattern)
function isFile(path) {
    return extension(path) !== ""
}

/// Conform 'path' to the Qt file representation relying on "file:" protocol prefix
function stringToFile(path) {
    // already containing the file protocol
    if(path.startsWith("file:"))
        return path
    // network path
    if(path.startsWith("//"))
        return "file:" + path
    // assumed local path
    if(path.trim() == "")
        return ""
    return "file:/" + path
}

/// Remove any "file:" protocol prefix from 'path'
function fileToString(path)
{
    // local path
    if(path.startsWith("file:///"))
        return path.replace("file:///", "")
    // network path
    else if(path.startsWith("file://"))
        return path.replace("file://", "")
    return path
}
